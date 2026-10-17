import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../main";

function respuesta(datos, estado = 200) {
  return { ok: estado >= 200 && estado < 300, status: estado, json: async () => datos };
}

function responderCarga(url) {
  if (url.includes("/api/conversaciones")) return respuesta([]);
  if (url.includes("/api/resumen")) return respuesta({ total_ordenes: 4, en_espera_material: 1, materiales_sin_stock: 1, orden_mayor_prioridad: "45001234" });
  if (url.includes("/api/estado")) return respuesta({ disponible: true, base_datos: true, ollama: true });
  throw new Error(`Ruta no esperada: ${url}`);
}

function iniciarSesion(rol = "operador") {
  localStorage.setItem("sesion-sap", JSON.stringify({ token: "token-prueba", usuario: "operador", rol }));
}

function enviarConsulta(texto = "Cual es el stock de MAT-003?") {
  fireEvent.change(screen.getByPlaceholderText("Escribi una consulta de mantenimiento..."), { target: { value: texto } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

afterEach(() => vi.useRealTimers());

describe("App", () => {
  it("inicia sesion y carga el panel", async () => {
    globalThis.fetch = vi.fn((url) => {
      if (url.endsWith("/api/login")) return Promise.resolve(respuesta({ token: "token-prueba", usuario: "operador", rol: "operador" }));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "operador" } });
    fireEvent.change(screen.getByLabelText("Contrasena"), { target: { value: "contrasena-segura" } });
    fireEvent.click(screen.getByRole("button", { name: "Ingresar" }));

    expect(await screen.findByText("Centro de consultas")).toBeInTheDocument();
    expect(localStorage.getItem("sesion-sap")).toContain("token-prueba");
  });

  it("cierra la sesion cuando el chat responde 401", async () => {
    iniciarSesion();
    globalThis.fetch = vi.fn((url) => Promise.resolve(url.includes("/api/chat") ? respuesta({}, 401) : responderCarga(url)));
    render(<App />);

    enviarConsulta();

    expect(await screen.findByRole("heading", { name: "Iniciar sesion" })).toBeInTheDocument();
    expect(localStorage.getItem("sesion-sap")).toBeNull();
  });

  it("descarta una respuesta pendiente al crear una conversacion nueva", async () => {
    iniciarSesion();
    let resolverChat;
    globalThis.fetch = vi.fn((url) => {
      if (url.includes("/api/chat")) return new Promise((resolve) => { resolverChat = resolve; });
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    enviarConsulta();
    fireEvent.click(screen.getByRole("button", { name: "Nueva conversacion" }));
    await act(async () => resolverChat(respuesta({ respuesta: "Respuesta obsoleta", herramientas_usadas: [], conversacion_id: 9 })));

    expect(screen.queryByText("Respuesta obsoleta")).not.toBeInTheDocument();
    expect(screen.getByText("Inicia una conversacion con una consulta operativa.")).toBeInTheDocument();
  });

  it("mantiene la ultima conversacion elegida ante respuestas fuera de orden", async () => {
    iniciarSesion();
    let resolverPrimera;
    globalThis.fetch = vi.fn((url) => {
      if (url.endsWith("/api/conversaciones")) return Promise.resolve(respuesta([{ id: 1, titulo: "Primera", actualizado_en: "2026-10-16T10:00:00" }, { id: 2, titulo: "Segunda", actualizado_en: "2026-10-16T11:00:00" }]));
      if (url.endsWith("/api/conversaciones/1")) return new Promise((resolve) => { resolverPrimera = resolve; });
      if (url.endsWith("/api/conversaciones/2")) return Promise.resolve(respuesta({ id: 2, mensajes: [{ rol: "assistant", contenido: "Mensaje actual", creado_en: "2026-10-16T11:00:00" }] }));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /Primera/ }));
    fireEvent.click(screen.getByRole("button", { name: /Segunda/ }));
    expect(await screen.findByText("Mensaje actual")).toBeInTheDocument();
    await act(async () => resolverPrimera(respuesta({ id: 1, mensajes: [{ rol: "assistant", contenido: "Mensaje obsoleto", creado_en: "2026-10-16T10:00:00" }] })));

    expect(screen.queryByText("Mensaje obsoleto")).not.toBeInTheDocument();
    expect(screen.getByText("Mensaje actual")).toBeInTheDocument();
  });

  it("informa errores HTTP recuperables del chat", async () => {
    iniciarSesion();
    globalThis.fetch = vi.fn((url) => Promise.resolve(url.includes("/api/chat") ? respuesta({}, 503) : responderCarga(url)));
    render(<App />);

    enviarConsulta();

    expect(await screen.findByText(/La API no pudo procesar la consulta/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
  });

  it("muestra un error recuperable cuando el chat supera el timeout", async () => {
    vi.useFakeTimers();
    iniciarSesion();
    globalThis.fetch = vi.fn((url, opciones = {}) => {
      if (url.includes("/api/chat")) return new Promise((_, reject) => opciones.signal.addEventListener("abort", () => reject(new DOMException("Abortada", "AbortError"))));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    enviarConsulta();
    await act(async () => vi.advanceTimersByTimeAsync(60000));

    expect(screen.getByText("La consulta tardo demasiado. Intenta nuevamente.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeEnabled();
  });

  it("muestra los controles administrativos solo a administradores", async () => {
    iniciarSesion("operador");
    globalThis.fetch = vi.fn((url) => Promise.resolve(responderCarga(url)));
    const vista = render(<App />);

    expect(screen.queryByRole("button", { name: "Cuentas" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Auditoria" })).not.toBeInTheDocument();
    vista.unmount();

    iniciarSesion("administrador");
    render(<App />);

    expect(await screen.findByRole("button", { name: "Cuentas" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Auditoria" })).toBeInTheDocument();
  });

  it("asocia etiquetas a los campos de creacion de cuentas", async () => {
    iniciarSesion("administrador");
    globalThis.fetch = vi.fn((url) => Promise.resolve(responderCarga(url)));
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Cuentas" }));

    expect(screen.getByLabelText("Usuario")).toBeInTheDocument();
    expect(screen.getByLabelText("Contrasena")).toBeInTheDocument();
    expect(screen.getByLabelText("Rol")).toBeInTheDocument();
  });

  it("elimina la conversacion activa despues de confirmar", async () => {
    iniciarSesion();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    globalThis.fetch = vi.fn((url, opciones = {}) => {
      if (url.endsWith("/api/conversaciones")) return Promise.resolve(respuesta([{ id: 3, titulo: "Consulta", actualizado_en: "2026-10-16T10:00:00" }]));
      if (url.endsWith("/api/conversaciones/3") && opciones.method === "DELETE") return Promise.resolve(respuesta({}, 204));
      if (url.endsWith("/api/conversaciones/3")) return Promise.resolve(respuesta({ id: 3, mensajes: [] }));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /Consulta/ }));
    expect(await screen.findByRole("button", { name: "Eliminar conversacion" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Eliminar conversacion" }));

    expect(await screen.findByText("Inicia una conversacion con una consulta operativa.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Eliminar conversacion" })).not.toBeInTheDocument();
  });

  it("permite a un administrador restablecer la contrasena de otra cuenta", async () => {
    iniciarSesion("administrador");
    globalThis.fetch = vi.fn((url, opciones = {}) => {
      if (url.endsWith("/api/cuentas") && !opciones.method) return Promise.resolve(respuesta([{ usuario: "tecnico", rol: "operador", creado_en: "2026-10-16T10:00:00" }]));
      if (url.endsWith("/api/cuentas/tecnico/contrasena")) return Promise.resolve(respuesta({}, 204));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Cuentas" }));
    fireEvent.click(await screen.findByRole("button", { name: "Restablecer contrasena" }));
    fireEvent.change(screen.getByLabelText("Nueva contrasena para tecnico"), { target: { value: "contrasena-nueva" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar contrasena" }));

    expect(await screen.findByRole("button", { name: "Restablecer contrasena" })).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringMatching(/tecnico\/contrasena$/), expect.objectContaining({ method: "PATCH" }));
  });

  it("muestra y permite atender alertas pendientes", async () => {
    iniciarSesion();
    globalThis.fetch = vi.fn((url, opciones = {}) => {
      if (url.endsWith("/api/alertas") && !opciones.method) return Promise.resolve(respuesta([{ id: 4, equipo: "EQ-1001", descripcion_equipo: "Bomba", nivel: "Alto", puntaje: 80, detalle: "Aviso activo.", creada_por: "operador", creada_en: "2026-10-16T10:00:00" }]));
      if (url.endsWith("/api/alertas/4")) return Promise.resolve(respuesta({}, 204));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Alertas" }));
    expect(await screen.findByText(/EQ-1001 · Riesgo Alto/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Marcar atendida" }));

    expect(await screen.findByText("Sin alertas pendientes.")).toBeInTheDocument();
  });

  it("permite a un administrador incorporar un documento tecnico", async () => {
    iniciarSesion("administrador");
    globalThis.fetch = vi.fn((url, opciones = {}) => {
      if (url.endsWith("/api/documentos-tecnicos") && !opciones.method) return Promise.resolve(respuesta([]));
      if (url.endsWith("/api/documentos-tecnicos")) return Promise.resolve(respuesta({ id: 4, titulo: "Manual Bomba", fuente: "PM-BOM-01", contenido: "Verificar vibracion y sello mecanico.", creado_en: "2026-10-16T10:00:00" }, 201));
      return Promise.resolve(responderCarga(url));
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Documentos" }));
    fireEvent.change(screen.getByLabelText("Titulo"), { target: { value: "Manual Bomba" } });
    fireEvent.change(screen.getByLabelText("Fuente"), { target: { value: "PM-BOM-01" } });
    fireEvent.change(screen.getByLabelText("Contenido"), { target: { value: "Verificar vibracion y sello mecanico." } });
    fireEvent.click(screen.getByRole("button", { name: "Incorporar documento" }));

    expect(await screen.findByText("Manual Bomba")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringMatching(/documentos-tecnicos$/), expect.objectContaining({ method: "POST" }));
  });
});
