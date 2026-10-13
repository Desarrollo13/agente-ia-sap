import { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

const consultasRapidas = [
  "Cual es el stock de MAT-003?",
  "Que materiales estan sin stock?",
  "Que ordenes esperando material tienen mayor prioridad?",
];

function App() {
  const [pregunta, setPregunta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mensajes, setMensajes] = useState([
    {
      tipo: "asistente",
      contenido: "Listo para consultar ordenes, materiales, stock y prioridades de mantenimiento.",
      herramientas: [],
    },
  ]);

  async function enviarPregunta(evento) {
    evento?.preventDefault();
    const consulta = pregunta.trim();
    if (!consulta || cargando) return;

    setMensajes((actuales) => [...actuales, { tipo: "usuario", contenido: consulta }]);
    setPregunta("");
    setCargando(true);

    try {
      const respuesta = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta: consulta }),
      });
      if (!respuesta.ok) throw new Error("La API no pudo procesar la consulta.");

      const datos = await respuesta.json();
      setMensajes((actuales) => [
        ...actuales,
        {
          tipo: "asistente",
          contenido: datos.respuesta,
          herramientas: datos.herramientas_usadas,
        },
      ]);
    } catch (error) {
      setMensajes((actuales) => [
        ...actuales,
        {
          tipo: "error",
          contenido: `${error.message} Verifica que FastAPI este ejecutandose en ${API_URL}.`,
          herramientas: [],
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
        <div className="estado"><i /> Sistema disponible</div>
        <div className="panel-dato"><strong>Fuente</strong><span>MySQL + Ollama</span></div>
        <div className="panel-dato"><strong>Modelo</strong><span>qwen2.5:3b</span></div>
      </aside>

      <section className="chat">
        <header><div><p className="etiqueta">ASISTENTE</p><h2>Centro de consultas</h2></div><span className="fecha">Mantenimiento SAP</span></header>
        <div className="mensajes">
          {mensajes.map((mensaje, indice) => (
            <article className={`mensaje ${mensaje.tipo}`} key={indice}>
              <span className="rol">{mensaje.tipo === "usuario" ? "Operador" : "Agente"}</span>
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
