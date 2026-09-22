DROP DATABASE IF EXISTS thermal_monitoring;
CREATE DATABASE thermal_monitoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE thermal_monitoring;
CREATE TABLE usuarios (
    usuario_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
    correo_electronico VARCHAR(100) UNIQUE NOT NULL,
    hash_contrasena VARCHAR(1024) NOT NULL,
    rol ENUM('admin', 'operador') DEFAULT 'operador',
    INDEX idx_nombre_usuario (nombre_usuario)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE eventos (
    evento_id INT AUTO_INCREMENT PRIMARY KEY,
    fecha_evento DATE NOT NULL,
    descripcion TEXT,
    estatus ENUM('confirmado', 'descartado', 'pendiente') DEFAULT 'pendiente',
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE
    SET NULL,
        INDEX idx_fecha_evento (fecha_evento)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE imagenes (
    imagen_id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id INT,
    ruta_imagen VARCHAR(255) NOT NULL,
    hora_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evento_id) REFERENCES eventos(evento_id) ON DELETE CASCADE,
    INDEX idx_hora_subida (hora_subida),
    INDEX idx_evento_id (evento_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE detecciones (
    deteccion_id INT AUTO_INCREMENT PRIMARY KEY,
    imagen_id INT,
    confianza FLOAT NOT NULL,
    x1 INT NOT NULL,
    y1 INT NOT NULL,
    x2 INT NOT NULL,
    y2 INT NOT NULL,
    FOREIGN KEY (imagen_id) REFERENCES imagenes(imagen_id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE calidad_aire (
    registro_id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id INT,
    hora_medicion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temp FLOAT,
    humedad FLOAT,
    pm2p5 FLOAT,
    pm10 FLOAT,
    pm1p0 FLOAT,
    aqi FLOAT,
    descrip VARCHAR(30),
    tipo ENUM('antes', 'durante', 'despues', 'pendiente') DEFAULT 'pendiente',
    FOREIGN KEY (evento_id) REFERENCES eventos(evento_id) ON DELETE CASCADE,
    INDEX idx_hora_medicion (hora_medicion),
    INDEX idx_evento_id (evento_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE logs_sistema (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('info', 'advertencia', 'error') DEFAULT 'info',
    mensaje TEXT NOT NULL,
    hora_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hora_log (hora_log)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
CREATE TABLE password_reset_tokens (
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_fecha_expiracion (fecha_expiracion)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
INSERT INTO usuarios (
        nombre_usuario,
        correo_electronico,
        hash_contrasena,
        rol
    )
VALUES (
        'userweb',
        'user@web.com',
        '$2b$12$alKQXNqjAyk2LEYdNsX.DevOQIbCO5hPGVAJmwstADFfKs6Cwtx2m',
        'operador'
    );
    
    
    
    
    
    
    
    
--  consultas eventos
select *
from eventos;
SELECT e.evento_id,
    e.fecha_evento,
    e.estatus,
    e.descripcion AS descripcion_evento,
    u.usuario_id,
    u.nombre_usuario,
    u.correo_electronico,
    i.imagen_id,
    i.ruta_imagen,
    i.hora_subida,
    d.deteccion_id,
    d.confianza,
    d.x1,
    d.y1,
    d.x2,
    d.y2,
    ca.registro_id,
    ca.hora_medicion,
    ca.temp,
    ca.humedad,
    ca.pm2p5,
    ca.pm10,
    ca.pm1p0,
    ca.aqi,
    ca.descrip AS descripcion_aire,
    ca.tipo AS tipo_medicion
FROM eventos e
    LEFT JOIN usuarios u ON u.usuario_id = e.usuario_id
    LEFT JOIN imagenes i ON i.evento_id = e.evento_id
    LEFT JOIN detecciones d ON d.imagen_id = i.imagen_id
    LEFT JOIN calidad_aire ca ON ca.evento_id = e.evento_id
ORDER BY e.fecha_evento DESC,
    e.evento_id DESC,
    i.imagen_id ASC,
    d.deteccion_id ASC;
    
    
    
    
-- por evento
SELECT e.*,
    i.*,
    d.*,
    ca.*
FROM eventos e
    LEFT JOIN imagenes i ON i.evento_id = e.evento_id
    LEFT JOIN detecciones d ON d.imagen_id = i.imagen_id
    LEFT JOIN calidad_aire ca ON ca.evento_id = e.evento_id
WHERE e.evento_id = 2;