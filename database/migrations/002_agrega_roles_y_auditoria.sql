ALTER TABLE cuentas
    ADD COLUMN rol VARCHAR(20) NOT NULL DEFAULT 'operador' AFTER contrasena_cifrada;

UPDATE cuentas SET rol = 'administrador' WHERE usuario = 'admin';

CREATE TABLE auditoria (
    id INT NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(50) NOT NULL,
    evento VARCHAR(50) NOT NULL,
    detalle VARCHAR(255) NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_auditoria_usuario_fecha (usuario, creado_en),
    CONSTRAINT fk_auditoria_cuentas FOREIGN KEY (usuario) REFERENCES cuentas(usuario)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
