CREATE TABLE IF NOT EXISTS intentos_login (
    id INT NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(50) NOT NULL,
    direccion_ip VARCHAR(45) NOT NULL,
    exitoso BOOLEAN NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_intentos_login_control (usuario, direccion_ip, exitoso, creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_sesiones_vence_en ON sesiones(vence_en);
CREATE INDEX idx_conversaciones_usuario_fecha ON conversaciones(usuario, actualizado_en);
CREATE INDEX idx_mensajes_conversacion ON mensajes_conversacion(conversacion_id, id);
