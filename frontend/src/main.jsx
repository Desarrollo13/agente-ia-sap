import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const consultasRapidas = [
  "Cual es el stock de MAT-003?",
  "Que materiales estan sin stock?",
  "Que ordenes esperando material tienen mayor prioridad?",
];

const MENSAJE_INICIAL = {
  tipo: "asistente",
  contenido: "Listo para consultar ordenes, materiales, stock y prioridades de mantenimiento.",
  herramientas: [],
  hora: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
};

function cargarHistorial() {
  try {
    return JSON.parse(localStorage.getItem("historial-sap")) ?? [MENSAJE_INICIAL];
  } catch {
    return [MENSAJE_INICIAL];
  }
}

function App() {
  const [pregunta, setPregunta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mensajes, setMensajes] = useState(cargarHistorial);
  const [resumen, setResumen] = useState(null);
  const [errorResumen, setErrorResumen] = useState(false);
  const [estadoServicios, setEstadoServicios] = useState(null);

  useEffect(() => {
    localStorage.setItem("historial-sap", JSON.stringify(mensajes));
  }, [mensajes]);

  async function cargarResumen() {
    try {
      const respuesta = await fetch(`${API_URL}/api/resumen`);
      if (!respuesta.ok) throw new Error();
      setResumen(await respuesta.json());
      setErrorResumen(false);
    } catch {
      setErrorResumen(true);
    }
  }

  async function cargarEstado() {
    try {
      const respuesta = await fetch(`${API_URL}/api/estado`);
      if (!respuesta.ok) throw new Error();
      setEstadoServicios(await respuesta.json());
    } catch {
      setEstadoServicios({ disponible: false, base_datos: false, ollama: false });
    }
  }

  useEffect(() => {
    cargarResumen();
    cargarEstado();
  }, []);

  async function enviarPregunta(evento) {
    evento?.preventDefault();
    const consulta = pregunta.trim();
    if (!consulta || cargando) return;

    setMensajes((actuales) => [...actuales, { tipo: "usuario", contenido: consulta, hora: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }]);
    setPregunta("");
    setCargando(true);

    try {
      const respuesta = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pregunta: consulta,
          historial: mensajes
            .filter((mensaje) => mensaje.tipo === "usuario" || mensaje.tipo === "asistente")
            .slice(-10)
            .map((mensaje) => ({
              role: mensaje.tipo === "usuario" ? "user" : "assistant",
              content: mensaje.contenido,
            })),
        }),
      });
      if (!respuesta.ok) throw new Error("La API no pudo procesar la consulta.");

      const datos = await respuesta.json();
      setMensajes((actuales) => [
        ...actuales,
        {
          tipo: "asistente",
          contenido: datos.respuesta,
          herramientas: datos.herramientas_usadas,
          hora: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (error) {
      const mensaje = error instanceof TypeError
        ? "No se pudo conectar con la API."
        : error.message;
      setMensajes((actuales) => [
        ...actuales,
        {
          tipo: "error",
          contenido: `${mensaje} Verifica que FastAPI este ejecutandose en ${API_URL}.`,
          herramientas: [],
          hora: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setCargando(false);
    }
  }

  return (
    <main className="aplicacion">
      <aside className="panel-lateral">
        <div className="marca"><span>AI</span> SAP Mantenimiento</div>
        <p className="etiqueta">CONSOLA OPERATIVA</p>
        <h1>Consulta el estado de planta.</h1>
        <p className="descripcion">Datos de ordenes, materiales y stock conectados a MySQL.</p>
        <div className={`estado ${estadoServicios?.disponible ? "correcto" : "error"}`}><i /> {estadoServicios ? (estadoServicios.disponible ? "Sistema disponible" : "Servicio no disponible") : "Verificando sistema"}</div>
        <div className="panel-dato"><strong>Fuente</strong><span>MySQL {estadoServicios?.base_datos ? "conectado" : "sin conexion"}</span></div>
        <div className="panel-dato"><strong>Modelo</strong><span>qwen2.5:3b {estadoServicios?.ollama ? "disponible" : "no disponible"}</span></div>
      </aside>

      <section className="chat">
        <header><div><p className="etiqueta">ASISTENTE</p><h2>Centro de consultas</h2></div><button className="nueva-conversacion" onClick={() => setMensajes([{ ...MENSAJE_INICIAL, hora: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }])}>Nueva conversacion</button></header>
        <section className="indicadores">
          <div><span>Total ordenes</span><strong>{resumen?.total_ordenes ?? "-"}</strong></div>
          <div><span>En espera</span><strong>{resumen?.en_espera_material ?? "-"}</strong></div>
          <div><span>Sin stock</span><strong>{resumen?.materiales_sin_stock ?? "-"}</strong></div>
          <div><span>Prioridad alta</span><strong>{resumen?.orden_mayor_prioridad ?? "-"}</strong></div>
          <button className="actualizar" onClick={() => { cargarResumen(); cargarEstado(); }}>Actualizar</button>
          {errorResumen && <p>No se pudo actualizar el resumen.</p>}
        </section>
        <div className="mensajes">
          {mensajes.map((mensaje, indice) => (
            <article className={`mensaje ${mensaje.tipo}`} key={indice}>
              <span className="rol">{mensaje.tipo === "usuario" ? "Operador" : "Agente"} <time>{mensaje.hora}</time></span>
              <p>{mensaje.contenido}</p>
              {mensaje.herramientas?.length > 0 && <div className="herramientas">{mensaje.herramientas.map((herramienta) => <span key={herramienta}>{herramienta}</span>)}</div>}
            </article>
          ))}
          {cargando && <article className="mensaje asistente"><span className="rol">Agente</span><p className="cargando">Consultando datos operativos</p></article>}
        </div>
        <div className="consultas-rapidas">{consultasRapidas.map((consulta) => <button key={consulta} onClick={() => setPregunta(consulta)}>{consulta}</button>)}</div>
        <form onSubmit={enviarPregunta}><input value={pregunta} onChange={(evento) => setPregunta(evento.target.value)} placeholder="Escribi una consulta de mantenimiento..." disabled={cargando} /><button type="submit" disabled={cargando}>Enviar</button></form>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
