INSERT IGNORE INTO equipos (equipo, descripcion, ubicacion_tecnica, criticidad) VALUES
    ('EQ-1001', 'Bomba centrifuga de proceso', 'PLANTA-01-BOMBAS-01', 'Alta'),
    ('EQ-1002', 'Motor electrico de impulsion', 'PLANTA-01-MOTORES-02', 'Media'),
    ('EQ-1003', 'Compresor de aire', 'PLANTA-02-AIRE-01', 'Alta');

INSERT IGNORE INTO ordenes (numero_orden, estado, prioridad, descripcion, equipo) VALUES
    ('45001234', 'En espera de material', 'Alta', 'Reparacion de bomba', 'EQ-1001'),
    ('45001235', 'En reparacion', 'Media', 'Mantenimiento de motor', 'EQ-1002'),
    ('45001236', 'Finalizada', 'Baja', 'Inspeccion de equipo', 'EQ-1003'),
    ('45001237', 'En espera de material', 'Media', 'Cambio de rodamiento', 'EQ-1001');

INSERT IGNORE INTO usuarios (legajo, nombre, sector, estado) VALUES
    ('1001', 'Juan Perez', 'Mantenimiento', 'Activo'),
    ('1002', 'Maria Gonzalez', 'Calidad', 'Activo'),
    ('1003', 'Pedro Lopez', 'Compras', 'Inactivo');

INSERT IGNORE INTO materiales (material, descripcion, stock, unidad) VALUES
    ('MAT-001', 'Sello mecanico', 3, 'UN'),
    ('MAT-002', 'Rodamiento', 12, 'UN'),
    ('MAT-003', 'Aceite hidraulico', 0, 'L');

INSERT IGNORE INTO orden_materiales (numero_orden, material, cantidad_requerida) VALUES
    ('45001234', 'MAT-003', 2),
    ('45001235', 'MAT-002', 1),
    ('45001236', 'MAT-001', 1),
    ('45001237', 'MAT-002', 1);

INSERT IGNORE INTO avisos_falla (numero_aviso, equipo, numero_orden, fecha_aviso, estado, sintoma, modo_falla, causa) VALUES
    ('80000001', 'EQ-1001', '45001234', '2026-09-12 08:30:00', 'Abierto', 'Perdida de caudal y vibracion elevada', 'Falla de sello mecanico', 'Desgaste por operacion en seco'),
    ('80000002', 'EQ-1001', '45001237', '2026-08-03 14:15:00', 'Cerrado', 'Ruido anormal en el soporte', 'Desgaste de rodamiento', 'Lubricacion insuficiente'),
    ('80000003', 'EQ-1002', '45001235', '2026-09-20 11:00:00', 'En proceso', 'Temperatura elevada', 'Sobrecalentamiento', 'Ventilacion obstruida');
