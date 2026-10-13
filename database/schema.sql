CREATE TABLE IF NOT EXISTS ordenes (
    numero_orden VARCHAR(20) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    prioridad VARCHAR(20) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
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
