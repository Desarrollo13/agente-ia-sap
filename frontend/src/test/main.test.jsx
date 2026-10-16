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
});
