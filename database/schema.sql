CREATE TABLE IF NOT EXISTS equipos (
    equipo VARCHAR(20) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    ubicacion_tecnica VARCHAR(100) NOT NULL,
    criticidad ENUM('Alta', 'Media', 'Baja') NOT NULL,
    PRIMARY KEY (equipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ordenes (
    numero_orden VARCHAR(20) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    prioridad VARCHAR(20) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    equipo VARCHAR(20) NULL,
    INDEX idx_ordenes_equipo (equipo),
    CONSTRAINT fk_ordenes_equipos FOREIGN KEY (equipo) REFERENCES equipos (equipo),
    PRIMARY KEY (numero_orden)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios (
    legajo VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    PRIMARY KEY (legajo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS materiales (
    material VARCHAR(20) NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    stock INT NOT NULL,
    unidad VARCHAR(10) NOT NULL,
    PRIMARY KEY (material)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orden_materiales (
    numero_orden VARCHAR(20) NOT NULL,
    material VARCHAR(20) NOT NULL,
    cantidad_requerida INT NOT NULL,
    PRIMARY KEY (numero_orden, material),
    CONSTRAINT fk_orden_materiales_orden
        FOREIGN KEY (numero_orden) REFERENCES ordenes (numero_orden),
    CONSTRAINT fk_orden_materiales_material
        FOREIGN KEY (material) REFERENCES materiales (material)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS avisos_falla (
    numero_aviso VARCHAR(20) NOT NULL,
    equipo VARCHAR(20) NOT NULL,
    numero_orden VARCHAR(20) NULL,
    fecha_aviso DATETIME NOT NULL,
    estado VARCHAR(30) NOT NULL,
    sintoma VARCHAR(255) NOT NULL,
    modo_falla VARCHAR(100) NULL,
    causa VARCHAR(255) NULL,
    PRIMARY KEY (numero_aviso),
    INDEX idx_avisos_falla_equipo_fecha (equipo, fecha_aviso),
    CONSTRAINT fk_avisos_falla_equipo FOREIGN KEY (equipo) REFERENCES equipos (equipo),
    CONSTRAINT fk_avisos_falla_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero_orden)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
