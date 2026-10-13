INSERT IGNORE INTO ordenes (numero_orden, estado, prioridad, descripcion) VALUES
    ('45001234', 'En espera de material', 'Alta', 'Reparacion de bomba'),
    ('45001235', 'En reparacion', 'Media', 'Mantenimiento de motor'),
    ('45001236', 'Finalizada', 'Baja', 'Inspeccion de equipo'),
    ('45001237', 'En espera de material', 'Media', 'Cambio de rodamiento');

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
