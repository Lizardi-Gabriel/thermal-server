drop DATABASE IF EXISTS thermal_monitoring;
CREATE DATABASE thermal_monitoring
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE thermal_monitoring;


-- Tabla de usuarios
CREATE TABLE usuarios(
                         usuario_id INT AUTO_INCREMENT PRIMARY KEY,
                         nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
                         correo_electronico VARCHAR(100) UNIQUE NOT NULL,
                         hash_contrasena VARCHAR(1024) NOT NULL,
                         rol ENUM('admin', 'operador') DEFAULT 'operador',
                         INDEX idx_nombre_usuario (nombre_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- cada usuario confirma o descarta un eventos
-- un evento solo es confirmado o descartado por un usuario


-- tabla de eventos
-- cada evento tiene imagenes
-- una imagen solo pertenece a un evento
CREATE TABLE eventos(
                        evento_id INT AUTO_INCREMENT PRIMARY KEY,
                        fecha_evento DATE NOT NULL, -- fecha sin hora
                        descripcion TEXT, -- llm o manual añade descripcion del evento
                        estatus ENUM('confirmado', 'descartado', 'pendiente') DEFAULT 'pendiente', -- asigando por un usuario
                        usuario_id INT, -- usuario que confirma o descarta el evento
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE SET NULL,
                        INDEX idx_fecha_evento (fecha_evento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla imagenes, cada imagen tiene detecciones
-- cada deteccion pertenece a una imagen
CREATE TABLE imagenes(
                         imagen_id INT AUTO_INCREMENT PRIMARY KEY,
                         evento_id  INT,
                         ruta_imagen VARCHAR(255) NOT NULL,
                         hora_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY (evento_id) REFERENCES eventos(evento_id) ON DELETE CASCADE,
                         INDEX idx_hora_subida (hora_subida),
                         INDEX idx_evento_id (evento_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de detecciones
-- cada deteccion pertenece a una imagen
-- una imagen tiene muchas detecciones
CREATE TABLE detecciones(
                            deteccion_id INT AUTO_INCREMENT PRIMARY KEY,
                            imagen_id INT,
                            confianza FLOAT NOT NULL,
                            x1 INT NOT NULL,
                            y1 INT NOT NULL,
                            x2 INT NOT NULL,
                            y2 INT NOT NULL,
                            FOREIGN KEY (imagen_id) REFERENCES imagenes(imagen_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- tabla de calidad del aire
-- cada evento tiene un registro de calidad de aire antes, uno durante y uno despues del evento
CREATE TABLE calidad_aire(
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
                             tipo ENUM('antes', 'durante', 'despues', 'pendiente') default 'pendiente', -- asignado por sistema al detectar un evento
                             FOREIGN KEY (evento_id) REFERENCES eventos(evento_id) ON DELETE CASCADE,
                             INDEX idx_hora_medicion (hora_medicion),
                             INDEX idx_evento_id (evento_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- tabla de logs del sitema
CREATE TABLE logs_sistema(
                             log_id INT AUTO_INCREMENT PRIMARY KEY,
                             tipo ENUM('info', 'advertencia', 'error') default 'info',
                             mensaje TEXT NOT NULL,
                             hora_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             INDEX idx_hora_log (hora_log)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- tabla de tokens FCM para notificaciones push
CREATE TABLE tokens_fcm(
                           token_id INT AUTO_INCREMENT PRIMARY KEY,
                           usuario_id INT,
                           token_fcm VARCHAR(255) NOT NULL,
                           dispositivo VARCHAR(100),
                           fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           activo BOOLEAN DEFAULT TRUE,
                           FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
                           INDEX idx_usuario_id (usuario_id),
                           INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Tabla de tokens de recuperacion de contraseña
CREATE TABLE password_reset_tokens(
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- registrar usuario: password= password
INSERT INTO usuarios (nombre_usuario, correo_electronico, hash_contrasena, rol)
VALUES ('userweb', 'user@web.com', '$2b$12$alKQXNqjAyk2LEYdNsX.DevOQIbCO5hPGVAJmwstADFfKs6Cwtx2m', 'operador');


-- borrar un registro de eventos:
-- DELETE FROM eventos WHERE evento_id = 1;






/*
-- ejecucion modificar calidad del aire:

ALTER TABLE calidad_aire
    -- Renombrar pm25 a pm2p5 y quitar NOT NULL
    CHANGE COLUMN pm25 pm2p5 FLOAT,

    -- Modificar pm10 para quitar NOT NULL
    MODIFY COLUMN pm10 FLOAT,

    -- Renombrar pm01 a pm1p0 y quitar NOT NULL
    CHANGE COLUMN pm01 pm1p0 FLOAT,

    -- Agregar las nuevas columnas (que seran nulables por defecto)
    ADD COLUMN temp FLOAT AFTER hora_medicion,
    ADD COLUMN humedad FLOAT AFTER temp,
    ADD COLUMN aqi FLOAT AFTER pm1p0,
    ADD COLUMN descrip VARCHAR(30) AFTER aqi;
*/
