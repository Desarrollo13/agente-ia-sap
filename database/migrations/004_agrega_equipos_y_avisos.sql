CREATE TABLE IF NOT EXISTS equipos (
    equipo VARCHAR(20) NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    ubicacion_tecnica VARCHAR(100) NOT NULL,
    criticidad ENUM('Alta', 'Media', 'Baja') NOT NULL,
    PRIMARY KEY (equipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @agregar_columna_equipo = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE ordenes ADD COLUMN equipo VARCHAR(20) NULL',
        'SELECT 1'
    )
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordenes' AND COLUMN_NAME = 'equipo'
);
PREPARE sentencia FROM @agregar_columna_equipo;
EXECUTE sentencia;
DEALLOCATE PREPARE sentencia;

SET @agregar_indice_equipo = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE ordenes ADD INDEX idx_ordenes_equipo (equipo)',
        'SELECT 1'
    )
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordenes' AND INDEX_NAME = 'idx_ordenes_equipo'
);
PREPARE sentencia FROM @agregar_indice_equipo;
EXECUTE sentencia;
DEALLOCATE PREPARE sentencia;

SET @agregar_clave_foranea_equipo = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE ordenes ADD CONSTRAINT fk_ordenes_equipos FOREIGN KEY (equipo) REFERENCES equipos (equipo)',
        'SELECT 1'
    )
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ordenes'
        AND CONSTRAINT_NAME = 'fk_ordenes_equipos'
);
PREPARE sentencia FROM @agregar_clave_foranea_equipo;
EXECUTE sentencia;
DEALLOCATE PREPARE sentencia;

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

INSERT IGNORE INTO equipos (equipo, descripcion, ubicacion_tecnica, criticidad) VALUES
    ('EQ-1001', 'Bomba centrifuga de proceso', 'PLANTA-01-BOMBAS-01', 'Alta'),
    ('EQ-1002', 'Motor electrico de impulsion', 'PLANTA-01-MOTORES-02', 'Media'),
    ('EQ-1003', 'Compresor de aire', 'PLANTA-02-AIRE-01', 'Alta');

UPDATE ordenes SET equipo = CASE numero_orden
    WHEN '45001234' THEN 'EQ-1001'
    WHEN '45001235' THEN 'EQ-1002'
    WHEN '45001236' THEN 'EQ-1003'
    WHEN '45001237' THEN 'EQ-1001'
END
WHERE numero_orden IN ('45001234', '45001235', '45001236', '45001237');

INSERT IGNORE INTO avisos_falla (numero_aviso, equipo, numero_orden, fecha_aviso, estado, sintoma, modo_falla, causa) VALUES
    ('80000001', 'EQ-1001', '45001234', '2026-09-12 08:30:00', 'Abierto', 'Perdida de caudal y vibracion elevada', 'Falla de sello mecanico', 'Desgaste por operacion en seco'),
    ('80000002', 'EQ-1001', '45001237', '2026-08-03 14:15:00', 'Cerrado', 'Ruido anormal en el soporte', 'Desgaste de rodamiento', 'Lubricacion insuficiente'),
    ('80000003', 'EQ-1002', '45001235', '2026-09-20 11:00:00', 'En proceso', 'Temperatura elevada', 'Sobrecalentamiento', 'Ventilacion obstruida');
