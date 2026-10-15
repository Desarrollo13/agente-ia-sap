CREATE TABLE IF NOT EXISTS cuentas (
    usuario VARCHAR(50) NOT NULL,
    contrasena_cifrada VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sesiones (
    token_hash CHAR(64) NOT NULL,
    usuario VARCHAR(50) NOT NULL,
    vence_en DATETIME NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (token_hash),
    CONSTRAINT fk_sesiones_cuentas FOREIGN KEY (usuario) REFERENCES cuentas(usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS conversaciones (
    id INT NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(50) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_conversaciones_cuentas FOREIGN KEY (usuario) REFERENCES cuentas(usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS mensajes_conversacion (
    id INT NOT NULL AUTO_INCREMENT,
    conversacion_id INT NOT NULL,
    rol ENUM('user', 'assistant') NOT NULL,
    contenido TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_mensajes_conversaciones FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
