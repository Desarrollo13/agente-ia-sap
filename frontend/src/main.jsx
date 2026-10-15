import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const consultasRapidas = ["Cual es el stock de MAT-003?", "Que materiales estan sin stock?", "Que ordenes esperando material tienen mayor prioridad?"];

function horaDe(fecha) {
  return new Date(fecha).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fechaHoraDe(fecha) {
  return new Date(fecha).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
}

function App() {
  const [sesion, setSesion] = useState(() => { try { return JSON.parse(localStorage.getItem("sesion-sap")); } catch { return null; } });
  const [usuario, setUsuario] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [errorAcceso, setErrorAcceso] = useState("");
  const [pregunta, setPregunta] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mensajes, setMensajes] = useState([]);
  const [conversacionId, setConversacionId] = useState(null);
  const [conversaciones, setConversaciones] = useState([]);
  const [cargandoConversaciones, setCargandoConversaciones] = useState(false);
  const [errorConversaciones, setErrorConversaciones] = useState("");
  const [resumen, setResumen] = useState(null);
  const [errorResumen, setErrorResumen] = useState(false);
  const [estadoServicios, setEstadoServicios] = useState(null);
  const [auditoria, setAuditoria] = useState([]);
  const [mostrandoAuditoria, setMostrandoAuditoria] = useState(false);
  const [cargandoAuditoria, setCargandoAuditoria] = useState(false);
  const [errorAuditoria, setErrorAuditoria] = useState("");

  function encabezados() { return { Authorization: `Bearer ${sesion.token}` }; }
  function cerrarSesionLocal() {
    localStorage.removeItem("sesion-sap");
    setSesion(null); setConversacionId(null); setMensajes([]); setConversaciones([]); setAuditoria([]); setMostrandoAuditoria(false);
  }

  async function abrirConversacion(id) {
    setErrorConversaciones("");
    try {
      const respuesta = await fetch(`${API_URL}/api/conversaciones/${id}`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo abrir la conversacion.");
      const datos = await respuesta.json();
      setConversacionId(datos.id);
      localStorage.setItem(`conversacion-sap-${sesion.usuario}`, String(datos.id));
      setMensajes(datos.mensajes.map((mensaje) => ({
        tipo: mensaje.rol === "user" ? "usuario" : "asistente",
        contenido: mensaje.contenido,
        herramientas: [],
        hora: horaDe(mensaje.creado_en),
      })));
    } catch (error) { setErrorConversaciones(error.message || "No se pudo abrir la conversacion."); }
  }

  async function cargarConversaciones(abrirActiva = false) {
    setCargandoConversaciones(true); setErrorConversaciones("");
    try {
      const respuesta = await fetch(`${API_URL}/api/conversaciones`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo cargar el historial.");
      const datos = await respuesta.json();
      setConversaciones(datos);
      const activa = Number(localStorage.getItem(`conversacion-sap-${sesion.usuario}`));
      if (abrirActiva && activa && datos.some((conversacion) => conversacion.id === activa)) await abrirConversacion(activa);
    } catch (error) { setErrorConversaciones(error.message || "No se pudo cargar el historial.");
    } finally { setCargandoConversaciones(false); }
  }

  useEffect(() => {
    if (sesion) cargarConversaciones(true);
  }, [sesion]);

  useEffect(() => {
    if (sesion) { cargarResumen(); cargarEstado(); }
  }, [sesion]);

  async function iniciarSesion(evento) {
    evento.preventDefault(); setErrorAcceso("");
    try {
      const respuesta = await fetch(`${API_URL}/api/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ usuario, contrasena }) });
      if (!respuesta.ok) throw new Error("Usuario o contrasena incorrectos.");
      const nuevaSesion = await respuesta.json();
      localStorage.setItem("sesion-sap", JSON.stringify(nuevaSesion));
      setSesion(nuevaSesion); setMensajes([]); setConversacionId(null); setContrasena("");
    } catch (error) { setErrorAcceso(error.message || "No se pudo conectar con la API."); }
  }

  async function cerrarSesion() {
    try { await fetch(`${API_URL}/api/logout`, { method: "POST", headers: encabezados() }); } finally { cerrarSesionLocal(); }
  }

  async function cargarResumen() {
    try {
      const respuesta = await fetch(`${API_URL}/api/resumen`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error();
      setResumen(await respuesta.json()); setErrorResumen(false);
    } catch { setErrorResumen(true); }
  }

  async function cargarEstado() {
    try {
      const respuesta = await fetch(`${API_URL}/api/estado`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error();
      setEstadoServicios(await respuesta.json());
    } catch { setEstadoServicios({ disponible: false, base_datos: false, ollama: false }); }
  }

  async function cargarAuditoria() {
    setCargandoAuditoria(true); setErrorAuditoria("");
    try {
      const respuesta = await fetch(`${API_URL}/api/auditoria`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo cargar la auditoria.");
      setAuditoria(await respuesta.json());
    } catch (error) { setErrorAuditoria(error.message || "No se pudo cargar la auditoria.");
    } finally { setCargandoAuditoria(false); }
  }

  function alternarAuditoria() {
    const visible = !mostrandoAuditoria;
    setMostrandoAuditoria(visible);
    if (visible) cargarAuditoria();
  }

  function nuevaConversacion() {
    localStorage.removeItem(`conversacion-sap-${sesion.usuario}`);
    setConversacionId(null); setMensajes([]); setErrorConversaciones("");
  }

  async function enviarPregunta(evento) {
    evento.preventDefault();
    const consulta = pregunta.trim();
    if (!consulta || cargando) return;
    const hora = horaDe(new Date());
    setMensajes((actuales) => [...actuales, { tipo: "usuario", contenido: consulta, hora }]);
    setPregunta(""); setCargando(true);
    try {
      const respuesta = await fetch(`${API_URL}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify({ pregunta: consulta, conversacion_id: conversacionId }) });
      if (respuesta.status === 401) { cerrarSesionLocal(); return; }
      if (!respuesta.ok) throw new Error("La API no pudo procesar la consulta.");
      const datos = await respuesta.json();
      setConversacionId(datos.conversacion_id);
      localStorage.setItem(`conversacion-sap-${sesion.usuario}`, String(datos.conversacion_id));
      setMensajes((actuales) => [...actuales, { tipo: "asistente", contenido: datos.respuesta, herramientas: datos.herramientas_usadas, hora: horaDe(new Date()) }]);
      cargarConversaciones();
    } catch (error) {
      const contenido = error instanceof TypeError ? "No se pudo conectar con la API." : error.message;
      setMensajes((actuales) => [...actuales, { tipo: "error", contenido: `${contenido} Verifica que FastAPI este ejecutandose en ${API_URL}.`, herramientas: [], hora: horaDe(new Date()) }]);
    } finally { setCargando(false); }
  }

  if (!sesion) return <main className="acceso"><form className="formulario-acceso" onSubmit={iniciarSesion}>
    <div className="marca"><span>AI</span> SAP Mantenimiento</div><p className="etiqueta">ACCESO OPERATIVO</p><h1>Iniciar sesion</h1><p>Ingresa con la cuenta creada por el administrador.</p>
    <label>Usuario<input value={usuario} onChange={(evento) => setUsuario(evento.target.value)} autoComplete="username" required /></label>
    <label>Contrasena<input type="password" value={contrasena} onChange={(evento) => setContrasena(evento.target.value)} autoComplete="current-password" required /></label>
    {errorAcceso && <p className="error-acceso">{errorAcceso}</p>}<button type="submit">Ingresar</button>
  </form></main>;

  return <main className="aplicacion">
    <aside className="panel-lateral"><div className="marca"><span>AI</span> SAP Mantenimiento</div><p className="etiqueta">CONSOLA OPERATIVA</p><h1>Consulta el estado de planta.</h1><p className="descripcion">Datos de ordenes, materiales y stock conectados a MySQL.</p><div className={`estado ${estadoServicios?.disponible ? "correcto" : "error"}`}><i /> {estadoServicios ? (estadoServicios.disponible ? "Sistema disponible" : "Servicio no disponible") : "Verificando sistema"}</div><div className="panel-dato"><strong>Fuente</strong><span>MySQL {estadoServicios?.base_datos ? "conectado" : "sin conexion"}</span></div><div className="panel-dato"><strong>Modelo</strong><span>qwen2.5:3b {estadoServicios?.ollama ? "disponible" : "no disponible"}</span></div><section className="historial"><div className="historial-cabecera"><strong>Conversaciones</strong><button onClick={() => cargarConversaciones()}>Actualizar</button></div>{cargandoConversaciones && <p>Cargando historial...</p>}{errorConversaciones && <p className="error-historial">{errorConversaciones}</p>}{!cargandoConversaciones && !errorConversaciones && conversaciones.map((conversacion) => <button className={conversacion.id === conversacionId ? "conversacion activa" : "conversacion"} key={conversacion.id} onClick={() => abrirConversacion(conversacion.id)}><span>{conversacion.titulo}</span><time>{horaDe(conversacion.actualizado_en)}</time></button>)}</section></aside>
    <section className="chat"><header><div><p className="etiqueta">ASISTENTE · {sesion.usuario} · {sesion.rol ?? "operador"}</p><h2>Centro de consultas</h2></div><div className="acciones-cabecera">{sesion.rol === "administrador" && <button className="nueva-conversacion" onClick={alternarAuditoria}>{mostrandoAuditoria ? "Cerrar auditoria" : "Auditoria"}</button>}<button className="nueva-conversacion" onClick={nuevaConversacion}>Nueva conversacion</button><button className="nueva-conversacion" onClick={cerrarSesion}>Cerrar sesion</button></div></header>
      <section className="indicadores"><div><span>Total ordenes</span><strong>{resumen?.total_ordenes ?? "-"}</strong></div><div><span>En espera</span><strong>{resumen?.en_espera_material ?? "-"}</strong></div><div><span>Sin stock</span><strong>{resumen?.materiales_sin_stock ?? "-"}</strong></div><div><span>Prioridad alta</span><strong>{resumen?.orden_mayor_prioridad ?? "-"}</strong></div><button className="actualizar" onClick={() => { cargarResumen(); cargarEstado(); }}>Actualizar</button>{errorResumen && <p>No se pudo actualizar el resumen.</p>}</section>
      {mostrandoAuditoria && <section className="panel-auditoria"><div className="auditoria-cabecera"><div><p className="etiqueta">ADMINISTRACION</p><h3>Auditoria reciente</h3></div><button className="actualizar" onClick={cargarAuditoria} disabled={cargandoAuditoria}>Actualizar</button></div>{cargandoAuditoria && <p>Cargando eventos...</p>}{errorAuditoria && <p className="error-auditoria">{errorAuditoria}</p>}{!cargandoAuditoria && !errorAuditoria && <div className="tabla-auditoria"><div className="fila-auditoria encabezado-auditoria"><span>Fecha</span><span>Usuario</span><span>Evento</span><span>Detalle</span></div>{auditoria.length === 0 ? <p>Sin eventos registrados.</p> : auditoria.map((evento, indice) => <div className="fila-auditoria" key={`${evento.creado_en}-${indice}`}><time>{fechaHoraDe(evento.creado_en)}</time><span>{evento.usuario}</span><span>{evento.evento.replaceAll("_", " ")}</span><span>{evento.detalle ?? "-"}</span></div>)}</div>}</section>}
      <div className="mensajes">{mensajes.length === 0 && <p className="sin-mensajes">Inicia una conversacion con una consulta operativa.</p>}{mensajes.map((mensaje, indice) => <article className={`mensaje ${mensaje.tipo}`} key={indice}><span className="rol">{mensaje.tipo === "usuario" ? "Operador" : "Agente"} <time>{mensaje.hora}</time></span><p>{mensaje.contenido}</p>{mensaje.herramientas?.length > 0 && <div className="herramientas">{mensaje.herramientas.map((herramienta) => <span key={herramienta}>{herramienta}</span>)}</div>}</article>)}{cargando && <article className="mensaje asistente"><span className="rol">Agente</span><p className="cargando">Consultando datos operativos</p></article>}</div>
      <div className="consultas-rapidas">{consultasRapidas.map((consulta) => <button key={consulta} onClick={() => setPregunta(consulta)}>{consulta}</button>)}</div><form onSubmit={enviarPregunta}><input value={pregunta} onChange={(evento) => setPregunta(evento.target.value)} placeholder="Escribi una consulta de mantenimiento..." disabled={cargando} /><button type="submit" disabled={cargando}>Enviar</button></form>
    </section>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
