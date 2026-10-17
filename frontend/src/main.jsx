import { useEffect, useRef, useState } from "react";
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

export function App() {
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
  const [cuentas, setCuentas] = useState([]);
  const [mostrandoCuentas, setMostrandoCuentas] = useState(false);
  const [cargandoCuentas, setCargandoCuentas] = useState(false);
  const [errorCuentas, setErrorCuentas] = useState("");
  const [nuevaCuenta, setNuevaCuenta] = useState({ usuario: "", contrasena: "", rol: "operador" });
  const [cuentaRestablecer, setCuentaRestablecer] = useState(null);
  const [contrasenaRestablecida, setContrasenaRestablecida] = useState("");
  const [alertas, setAlertas] = useState([]);
  const [mostrandoAlertas, setMostrandoAlertas] = useState(false);
  const [equipoAlerta, setEquipoAlerta] = useState("");
  const [errorAlertas, setErrorAlertas] = useState("");
  const [documentos, setDocumentos] = useState([]);
  const [mostrandoDocumentos, setMostrandoDocumentos] = useState(false);
  const [nuevoDocumento, setNuevoDocumento] = useState({ titulo: "", fuente: "", contenido: "" });
  const [errorDocumentos, setErrorDocumentos] = useState("");
  const solicitudConversacion = useRef(0);
  const solicitudChat = useRef(0);
  const controladorChat = useRef(null);

  function encabezados() { return { Authorization: `Bearer ${sesion.token}` }; }
  function cancelarChatPendiente() {
    solicitudChat.current += 1;
    controladorChat.current?.abort();
    controladorChat.current = null;
    setCargando(false);
  }
  function cerrarSesionLocal() {
    solicitudConversacion.current += 1;
    cancelarChatPendiente();
    localStorage.removeItem("sesion-sap");
    setSesion(null); setConversacionId(null); setMensajes([]); setConversaciones([]); setAuditoria([]); setMostrandoAuditoria(false); setCuentas([]); setMostrandoCuentas(false); setCuentaRestablecer(null); setContrasenaRestablecida(""); setAlertas([]); setMostrandoAlertas(false); setDocumentos([]); setMostrandoDocumentos(false);
  }

  async function abrirConversacion(id) {
    const idSolicitud = ++solicitudConversacion.current;
    cancelarChatPendiente();
    setErrorConversaciones("");
    try {
      const respuesta = await fetch(`${API_URL}/api/conversaciones/${id}`, { headers: encabezados() });
      if (idSolicitud !== solicitudConversacion.current) return;
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo abrir la conversacion.");
      const datos = await respuesta.json();
      if (idSolicitud !== solicitudConversacion.current) return;
      setConversacionId(datos.id);
      localStorage.setItem(`conversacion-sap-${sesion.usuario}`, String(datos.id));
      setMensajes(datos.mensajes.map((mensaje) => ({
        tipo: mensaje.rol === "user" ? "usuario" : "asistente",
        contenido: mensaje.contenido,
        herramientas: [],
        hora: horaDe(mensaje.creado_en),
      })));
    } catch (error) { if (idSolicitud === solicitudConversacion.current) setErrorConversaciones(error.message || "No se pudo abrir la conversacion."); }
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
    setMostrandoAuditoria(visible); setMostrandoCuentas(false);
    if (visible) cargarAuditoria();
  }

  async function cargarCuentas() {
    setCargandoCuentas(true); setErrorCuentas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/cuentas`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudieron cargar las cuentas.");
      setCuentas(await respuesta.json());
    } catch (error) { setErrorCuentas(error.message || "No se pudieron cargar las cuentas.");
    } finally { setCargandoCuentas(false); }
  }

  function alternarCuentas() {
    const visible = !mostrandoCuentas;
    setMostrandoCuentas(visible); setMostrandoAuditoria(false);
    if (visible) cargarCuentas();
  }
  async function cargarDocumentos() {
    setErrorDocumentos("");
    try {
      const respuesta = await fetch(`${API_URL}/api/documentos-tecnicos`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudieron cargar los documentos.");
      setDocumentos(await respuesta.json());
    } catch (error) { setErrorDocumentos(error.message || "No se pudieron cargar los documentos."); }
  }
  function alternarDocumentos() {
    const visible = !mostrandoDocumentos;
    setMostrandoDocumentos(visible); setMostrandoCuentas(false); setMostrandoAuditoria(false);
    if (visible) cargarDocumentos();
  }
  async function crearDocumento(evento) {
    evento.preventDefault(); setErrorDocumentos("");
    try {
      const respuesta = await fetch(`${API_URL}/api/documentos-tecnicos`, { method: "POST", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify(nuevoDocumento) });
      if (respuesta.status === 401) return cerrarSesionLocal();
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.detail || "No se pudo crear el documento.");
      setNuevoDocumento({ titulo: "", fuente: "", contenido: "" });
      setDocumentos((actuales) => [datos, ...actuales]);
    } catch (error) { setErrorDocumentos(error.message || "No se pudo crear el documento."); }
  }
  async function cargarAlertas() {
    setErrorAlertas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/alertas`, { headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudieron cargar las alertas.");
      setAlertas(await respuesta.json());
    } catch (error) { setErrorAlertas(error.message || "No se pudieron cargar las alertas."); }
  }
  function alternarAlertas() {
    const visible = !mostrandoAlertas;
    setMostrandoAlertas(visible);
    if (visible) cargarAlertas();
  }
  async function crearAlerta(evento) {
    evento.preventDefault(); setErrorAlertas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/equipos/${encodeURIComponent(equipoAlerta.trim())}/alertas`, { method: "POST", headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.detail || "No se pudo crear la alerta.");
      if (!datos.creada) throw new Error(datos.motivo);
      setEquipoAlerta(""); cargarAlertas();
    } catch (error) { setErrorAlertas(error.message || "No se pudo crear la alerta."); }
  }
  async function atenderAlerta(id) {
    setErrorAlertas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/alertas/${id}`, { method: "PATCH", headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo atender la alerta.");
      setAlertas((actuales) => actuales.filter((alerta) => alerta.id !== id));
    } catch (error) { setErrorAlertas(error.message || "No se pudo atender la alerta."); }
  }

  async function crearCuenta(evento) {
    evento.preventDefault(); setErrorCuentas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/cuentas`, { method: "POST", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify(nuevaCuenta) });
      if (respuesta.status === 401) return cerrarSesionLocal();
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.detail || "No se pudo crear la cuenta.");
      setNuevaCuenta({ usuario: "", contrasena: "", rol: "operador" });
      cargarCuentas();
    } catch (error) { setErrorCuentas(error.message || "No se pudo crear la cuenta."); }
  }

  async function cambiarRol(usuario, rol) {
    setErrorCuentas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/cuentas/${encodeURIComponent(usuario)}`, { method: "PATCH", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify({ rol }) });
      if (respuesta.status === 401) return cerrarSesionLocal();
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.detail || "No se pudo actualizar el rol.");
      setCuentas((actuales) => actuales.map((cuenta) => cuenta.usuario === usuario ? { ...cuenta, rol: datos.rol } : cuenta));
    } catch (error) { setErrorCuentas(error.message || "No se pudo actualizar el rol."); }
  }
  async function restablecerContrasena(evento) {
    evento.preventDefault(); setErrorCuentas("");
    try {
      const respuesta = await fetch(`${API_URL}/api/cuentas/${encodeURIComponent(cuentaRestablecer)}/contrasena`, { method: "PATCH", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify({ contrasena: contrasenaRestablecida }) });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) { const datos = await respuesta.json(); throw new Error(datos.detail || "No se pudo restablecer la contrasena."); }
      setCuentaRestablecer(null); setContrasenaRestablecida("");
    } catch (error) { setErrorCuentas(error.message || "No se pudo restablecer la contrasena."); }
  }

  function nuevaConversacion() {
    solicitudConversacion.current += 1;
    cancelarChatPendiente();
    localStorage.removeItem(`conversacion-sap-${sesion.usuario}`);
    setConversacionId(null); setMensajes([]); setErrorConversaciones("");
  }
  async function eliminarConversacion() {
    if (!conversacionId || !window.confirm("Se eliminara esta conversacion y su historial. Deseas continuar?")) return;
    const idEliminada = conversacionId;
    solicitudConversacion.current += 1;
    cancelarChatPendiente();
    setErrorConversaciones("");
    try {
      const respuesta = await fetch(`${API_URL}/api/conversaciones/${idEliminada}`, { method: "DELETE", headers: encabezados() });
      if (respuesta.status === 401) return cerrarSesionLocal();
      if (!respuesta.ok) throw new Error("No se pudo eliminar la conversacion.");
      localStorage.removeItem(`conversacion-sap-${sesion.usuario}`);
      setConversacionId(null); setMensajes([]);
      setConversaciones((actuales) => actuales.filter((conversacion) => conversacion.id !== idEliminada));
    } catch (error) { setErrorConversaciones(error.message || "No se pudo eliminar la conversacion."); }
  }

  async function enviarPregunta(evento) {
    evento.preventDefault();
    const consulta = pregunta.trim();
    if (!consulta || cargando) return;
    const idSolicitud = ++solicitudChat.current;
    const conversacionSolicitada = conversacionId;
    const controlador = new AbortController();
    controladorChat.current = controlador;
    let tiempoAgotado = false;
    const timeout = window.setTimeout(() => { tiempoAgotado = true; controlador.abort(); }, 60000);
    const hora = horaDe(new Date());
    setMensajes((actuales) => [...actuales, { tipo: "usuario", contenido: consulta, hora }]);
    setPregunta(""); setCargando(true);
    try {
      const respuesta = await fetch(`${API_URL}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json", ...encabezados() }, body: JSON.stringify({ pregunta: consulta, conversacion_id: conversacionSolicitada }), signal: controlador.signal });
      if (idSolicitud !== solicitudChat.current) return;
      if (respuesta.status === 401) { cerrarSesionLocal(); return; }
      if (!respuesta.ok) throw new Error("La API no pudo procesar la consulta.");
      const datos = await respuesta.json();
      if (idSolicitud !== solicitudChat.current) return;
      setConversacionId(datos.conversacion_id);
      localStorage.setItem(`conversacion-sap-${sesion.usuario}`, String(datos.conversacion_id));
      setMensajes((actuales) => [...actuales, { tipo: "asistente", contenido: datos.respuesta, herramientas: datos.herramientas_usadas, hora: horaDe(new Date()) }]);
      cargarConversaciones();
    } catch (error) {
      if (idSolicitud !== solicitudChat.current || error.name === "AbortError" && !tiempoAgotado) return;
      const contenido = tiempoAgotado ? "La consulta tardo demasiado. Intenta nuevamente." : error instanceof TypeError ? "No se pudo conectar con la API." : error.message;
      setMensajes((actuales) => [...actuales, { tipo: "error", contenido: tiempoAgotado ? contenido : `${contenido} Verifica que FastAPI este ejecutandose en ${API_URL}.`, herramientas: [], hora: horaDe(new Date()) }]);
    } finally {
      window.clearTimeout(timeout);
      if (idSolicitud === solicitudChat.current) {
        controladorChat.current = null;
        setCargando(false);
      }
    }
  }

  if (!sesion) return <main className="acceso"><form className="formulario-acceso" onSubmit={iniciarSesion}>
    <div className="marca"><span>AI</span> SAP Mantenimiento</div><p className="etiqueta">ACCESO OPERATIVO</p><h1>Iniciar sesion</h1><p>Ingresa con la cuenta creada por el administrador.</p>
    <label>Usuario<input value={usuario} onChange={(evento) => setUsuario(evento.target.value)} autoComplete="username" required /></label>
    <label>Contrasena<input type="password" value={contrasena} onChange={(evento) => setContrasena(evento.target.value)} autoComplete="current-password" required /></label>
    {errorAcceso && <p className="error-acceso">{errorAcceso}</p>}<button type="submit">Ingresar</button>
  </form></main>;

  return <main className="aplicacion">
    <aside className="panel-lateral"><div className="marca"><span>AI</span> SAP Mantenimiento</div><p className="etiqueta">CONSOLA OPERATIVA</p><h1>Consulta el estado de planta.</h1><p className="descripcion">Datos de ordenes, materiales y stock conectados a MySQL.</p><div className={`estado ${estadoServicios?.disponible ? "correcto" : "error"}`} role="status"><i /> {estadoServicios ? (estadoServicios.disponible ? "Sistema disponible" : "Servicio no disponible") : "Verificando sistema"}</div><div className="panel-dato"><strong>Fuente</strong><span>MySQL {estadoServicios?.base_datos ? "conectado" : "sin conexion"}</span></div><div className="panel-dato"><strong>Modelo</strong><span>qwen2.5:3b {estadoServicios?.ollama ? "disponible" : "no disponible"}</span></div><section className="historial"><div className="historial-cabecera"><strong>Conversaciones</strong><button onClick={() => cargarConversaciones()}>Actualizar</button></div>{cargandoConversaciones && <p role="status">Cargando historial...</p>}{errorConversaciones && <p className="error-historial" role="alert">{errorConversaciones}</p>}{!cargandoConversaciones && !errorConversaciones && conversaciones.map((conversacion) => <button className={conversacion.id === conversacionId ? "conversacion activa" : "conversacion"} key={conversacion.id} onClick={() => abrirConversacion(conversacion.id)}><span>{conversacion.titulo}</span><time>{horaDe(conversacion.actualizado_en)}</time></button>)}</section></aside>
    <section className="chat"><header><div><p className="etiqueta">ASISTENTE · {sesion.usuario} · {sesion.rol ?? "operador"}</p><h2>Centro de consultas</h2></div><div className="acciones-cabecera"><button className="nueva-conversacion" onClick={alternarAlertas}>{mostrandoAlertas ? "Cerrar alertas" : "Alertas"}</button>{sesion.rol === "administrador" && <button className="nueva-conversacion" onClick={alternarDocumentos}>{mostrandoDocumentos ? "Cerrar documentos" : "Documentos"}</button>}{sesion.rol === "administrador" && <button className="nueva-conversacion" onClick={alternarCuentas}>{mostrandoCuentas ? "Cerrar cuentas" : "Cuentas"}</button>}{sesion.rol === "administrador" && <button className="nueva-conversacion" onClick={alternarAuditoria}>{mostrandoAuditoria ? "Cerrar auditoria" : "Auditoria"}</button>}<button className="nueva-conversacion" onClick={nuevaConversacion}>Nueva conversacion</button>{conversacionId && <button className="eliminar-conversacion" onClick={eliminarConversacion}>Eliminar conversacion</button>}<button className="nueva-conversacion" onClick={cerrarSesion}>Cerrar sesion</button></div></header>
      <section className="indicadores"><div><span>Total ordenes</span><strong>{resumen?.total_ordenes ?? "-"}</strong></div><div><span>En espera</span><strong>{resumen?.en_espera_material ?? "-"}</strong></div><div><span>Sin stock</span><strong>{resumen?.materiales_sin_stock ?? "-"}</strong></div><div><span>Prioridad alta</span><strong>{resumen?.orden_mayor_prioridad ?? "-"}</strong></div><button className="actualizar" onClick={() => { cargarResumen(); cargarEstado(); }}>Actualizar</button>{errorResumen && <p>No se pudo actualizar el resumen.</p>}</section>
      {mostrandoCuentas && <section className="panel-cuentas"><div className="auditoria-cabecera"><div><p className="etiqueta">ADMINISTRACION</p><h3>Gestion de cuentas</h3></div><button className="actualizar" onClick={cargarCuentas} disabled={cargandoCuentas}>Actualizar</button></div><form className="formulario-cuenta" onSubmit={crearCuenta}><label>Usuario<input value={nuevaCuenta.usuario} onChange={(evento) => setNuevaCuenta({ ...nuevaCuenta, usuario: evento.target.value })} required /></label><label>Contrasena<input type="password" value={nuevaCuenta.contrasena} onChange={(evento) => setNuevaCuenta({ ...nuevaCuenta, contrasena: evento.target.value })} autoComplete="new-password" required /></label><label>Rol<select value={nuevaCuenta.rol} onChange={(evento) => setNuevaCuenta({ ...nuevaCuenta, rol: evento.target.value })}><option value="operador">Operador</option><option value="administrador">Administrador</option></select></label><button type="submit">Crear cuenta</button></form>{errorCuentas && <p className="error-auditoria" role="alert">{errorCuentas}</p>}{cargandoCuentas && <p role="status">Cargando cuentas...</p>}{!cargandoCuentas && !errorCuentas && <div className="tabla-cuentas"><div className="fila-cuenta encabezado-cuenta"><span>Usuario</span><span>Creada</span><span>Rol</span><span>Acciones</span></div>{cuentas.map((cuenta) => <div key={cuenta.usuario}><div className="fila-cuenta"><span>{cuenta.usuario}</span><time>{fechaHoraDe(cuenta.creado_en)}</time><select aria-label={`Rol de ${cuenta.usuario}`} value={cuenta.rol} disabled={cuenta.usuario === sesion.usuario} onChange={(evento) => cambiarRol(cuenta.usuario, evento.target.value)}><option value="operador">Operador</option><option value="administrador">Administrador</option></select>{cuenta.usuario !== sesion.usuario && <button className="restablecer-contrasena" onClick={() => { setCuentaRestablecer(cuenta.usuario); setContrasenaRestablecida(""); }}>Restablecer contrasena</button>}</div>{cuentaRestablecer === cuenta.usuario && <form className="formulario-restablecer" onSubmit={restablecerContrasena}><label>Nueva contrasena para {cuenta.usuario}<input type="password" value={contrasenaRestablecida} onChange={(evento) => setContrasenaRestablecida(evento.target.value)} autoComplete="new-password" minLength="10" required /></label><button type="submit">Guardar contrasena</button><button type="button" className="cancelar-restablecimiento" onClick={() => { setCuentaRestablecer(null); setContrasenaRestablecida(""); }}>Cancelar</button></form>}</div>)}</div>}</section>}
      {mostrandoAlertas && <section className="panel-alertas"><div className="auditoria-cabecera"><div><p className="etiqueta">MANTENIMIENTO</p><h3>Alertas de riesgo pendientes</h3></div><button className="actualizar" onClick={cargarAlertas}>Actualizar</button></div><form className="formulario-alerta" onSubmit={crearAlerta}><label>Equipo<input value={equipoAlerta} onChange={(evento) => setEquipoAlerta(evento.target.value)} placeholder="Ej.: EQ-1001" required /></label><button type="submit">Evaluar y crear alerta</button></form>{errorAlertas && <p className="error-auditoria" role="alert">{errorAlertas}</p>}<div className="tabla-alertas">{alertas.length === 0 ? <p>Sin alertas pendientes.</p> : alertas.map((alerta) => <article className="alerta" key={alerta.id}><div><strong>{alerta.equipo} · Riesgo {alerta.nivel} ({alerta.puntaje}/100)</strong><p>{alerta.descripcion_equipo}</p><p>{alerta.detalle}</p><time>{fechaHoraDe(alerta.creada_en)} · Creada por {alerta.creada_por}</time></div><button className="actualizar" onClick={() => atenderAlerta(alerta.id)}>Marcar atendida</button></article>)}</div></section>}
      {mostrandoDocumentos && <section className="panel-documentos"><div className="auditoria-cabecera"><div><p className="etiqueta">CONOCIMIENTO RAG</p><h3>Documentos tecnicos</h3></div><button className="actualizar" onClick={cargarDocumentos}>Actualizar</button></div><form className="formulario-documento" onSubmit={crearDocumento}><label>Titulo<input value={nuevoDocumento.titulo} onChange={(evento) => setNuevoDocumento({ ...nuevoDocumento, titulo: evento.target.value })} required /></label><label>Fuente<input value={nuevoDocumento.fuente} onChange={(evento) => setNuevoDocumento({ ...nuevoDocumento, fuente: evento.target.value })} placeholder="Ej.: Manual PM-BOM-01" required /></label><label>Contenido<textarea value={nuevoDocumento.contenido} onChange={(evento) => setNuevoDocumento({ ...nuevoDocumento, contenido: evento.target.value })} placeholder="Pega aqui el procedimiento tecnico..." minLength="20" required /></label><button type="submit">Incorporar documento</button></form>{errorDocumentos && <p className="error-auditoria" role="alert">{errorDocumentos}</p>}<div className="lista-documentos">{documentos.map((documento) => <article key={documento.id}><strong>{documento.titulo}</strong><span>Fuente: {documento.fuente}</span><p>{documento.contenido}</p><time>{fechaHoraDe(documento.creado_en)}</time></article>)}</div></section>}
      {mostrandoAuditoria && <section className="panel-auditoria"><div className="auditoria-cabecera"><div><p className="etiqueta">ADMINISTRACION</p><h3>Auditoria reciente</h3></div><button className="actualizar" onClick={cargarAuditoria} disabled={cargandoAuditoria}>Actualizar</button></div>{cargandoAuditoria && <p role="status">Cargando eventos...</p>}{errorAuditoria && <p className="error-auditoria" role="alert">{errorAuditoria}</p>}{!cargandoAuditoria && !errorAuditoria && <div className="tabla-auditoria"><div className="fila-auditoria encabezado-auditoria"><span>Fecha</span><span>Usuario</span><span>Evento</span><span>Detalle</span></div>{auditoria.length === 0 ? <p>Sin eventos registrados.</p> : auditoria.map((evento, indice) => <div className="fila-auditoria" key={`${evento.creado_en}-${indice}`}><time>{fechaHoraDe(evento.creado_en)}</time><span>{evento.usuario}</span><span>{evento.evento.replaceAll("_", " ")}</span><span>{evento.detalle ?? "-"}</span></div>)}</div>}</section>}
      <div className="mensajes">{mensajes.length === 0 && <p className="sin-mensajes">Inicia una conversacion con una consulta operativa.</p>}{mensajes.map((mensaje, indice) => <article className={`mensaje ${mensaje.tipo}`} key={indice}><span className="rol">{mensaje.tipo === "usuario" ? "Operador" : "Agente"} <time>{mensaje.hora}</time></span><p>{mensaje.contenido}</p>{mensaje.herramientas?.length > 0 && <div className="herramientas">{mensaje.herramientas.map((herramienta) => <span key={herramienta}>{herramienta}</span>)}</div>}</article>)}{cargando && <article className="mensaje asistente"><span className="rol">Agente</span><p className="cargando">Consultando datos operativos</p></article>}</div>
      <div className="consultas-rapidas">{consultasRapidas.map((consulta) => <button key={consulta} onClick={() => setPregunta(consulta)}>{consulta}</button>)}</div><form onSubmit={enviarPregunta}><label className="consulta-input"><span className="solo-lector">Consulta de mantenimiento</span><input value={pregunta} onChange={(evento) => setPregunta(evento.target.value)} placeholder="Escribi una consulta de mantenimiento..." disabled={cargando} /></label><button type="submit" disabled={cargando}>Enviar</button></form>
    </section>
  </main>;
}

const raiz = document.getElementById("root");
if (raiz) createRoot(raiz).render(<App />);
