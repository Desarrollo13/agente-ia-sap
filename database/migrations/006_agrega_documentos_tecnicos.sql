CREATE TABLE IF NOT EXISTS documentos_tecnicos (
    id INT NOT NULL AUTO_INCREMENT,
    titulo VARCHAR(255) NOT NULL,
    fuente VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_documentos_tecnicos_titulo_fuente (titulo, fuente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO documentos_tecnicos (titulo, fuente, contenido) VALUES
    ('Procedimiento de inspeccion de bomba centrifuga', 'Manual PM-BOM-01',
     'Ante perdida de caudal o vibracion elevada, detener el equipo segun el procedimiento de seguridad. Verificar nivel de lubricacion, alineacion del acoplamiento y condicion del sello mecanico. Si hay operacion en seco o fuga por sello, generar una orden correctiva y revisar la succion antes de reiniciar.'),
    ('Procedimiento de revision de rodamientos', 'Instructivo PM-ROD-02',
     'Ante ruido anormal, temperatura elevada o vibracion en el soporte, inspeccionar el rodamiento y su lubricacion. Confirmar la cantidad y tipo de grasa indicados por el fabricante. Reemplazar el rodamiento si presenta juego excesivo, picaduras o decoloracion por temperatura.'),
    ('Procedimiento de sobrecalentamiento de motores', 'Manual PM-MOT-03',
     'Ante sobrecalentamiento de un motor electrico, aislar la energia antes de intervenir. Revisar ventilacion, limpieza de rejillas, corriente de consumo y conexiones. No reiniciar el motor hasta eliminar la obstruccion y confirmar una temperatura de operacion normal.');
