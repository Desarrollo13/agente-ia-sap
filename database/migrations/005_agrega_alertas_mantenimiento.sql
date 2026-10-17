CREATE TABLE IF NOT EXISTS alertas_mantenimiento (
    id INT NOT NULL AUTO_INCREMENT,
    equipo VARCHAR(20) NOT NULL,
    nivel ENUM('Alto') NOT NULL,
    puntaje INT NOT NULL,
    detalle VARCHAR(1000) NOT NULL,
    estado ENUM('Pendiente', 'Atendida') NOT NULL DEFAULT 'Pendiente',
    creada_por VARCHAR(50) NOT NULL,
    creada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atendida_por VARCHAR(50) NULL,
    atendida_en DATETIME NULL,
    PRIMARY KEY (id),
    INDEX idx_alertas_equipo_estado (equipo, estado),
    INDEX idx_alertas_estado_fecha (estado, creada_en),
    CONSTRAINT fk_alertas_equipo FOREIGN KEY (equipo) REFERENCES equipos (equipo),
    CONSTRAINT fk_alertas_creada_por FOREIGN KEY (creada_por) REFERENCES cuentas (usuario),
    CONSTRAINT fk_alertas_atendida_por FOREIGN KEY (atendida_por) REFERENCES cuentas (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
