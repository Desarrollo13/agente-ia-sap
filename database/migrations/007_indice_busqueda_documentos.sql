SET @agregar_indice_documentos = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE documentos_tecnicos ADD FULLTEXT INDEX idx_documentos_tecnicos_busqueda (titulo, contenido)',
        'SELECT 1'
    )
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'documentos_tecnicos'
        AND INDEX_NAME = 'idx_documentos_tecnicos_busqueda'
);
PREPARE sentencia FROM @agregar_indice_documentos;
EXECUTE sentencia;
DEALLOCATE PREPARE sentencia;
