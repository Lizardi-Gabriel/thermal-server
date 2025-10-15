drop DATABASE IF EXISTS thermal_monitoring;
CREATE DATABASE thermal_monitoring
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE thermal_monitoring;

-- Tabla de usuarios
CREATE TABLE users (
                       user_id INT AUTO_INCREMENT PRIMARY KEY,
                       username VARCHAR(50) UNIQUE NOT NULL,
                       email VARCHAR(100) UNIQUE NOT NULL,
                       password_hash VARCHAR(255) NOT NULL,
                       role ENUM('admin', 'operador') DEFAULT 'operador',
                       INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Tabla imagenes con al menos una deteccion
create table images (
                        image_id INT AUTO_INCREMENT PRIMARY KEY,
                        image_path VARCHAR(255) NOT NULL,
                        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        number_of_detections INT DEFAULT 0,
                        INDEX idx_upload_time (upload_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de detecciones
CREATE TABLE detections (
                            detection_id INT AUTO_INCREMENT PRIMARY KEY,
                            image_id INT,
                            detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            confianza FLOAT NOT NULL,
                            x1 INT NOT NULL,
                            y1 INT NOT NULL,
                            x2 INT NOT NULL,
                            y2 INT NOT NULL,
                            FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE,
                            INDEX idx_detection_time (detection_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de confirmaciones
CREATE TABLE confirmations (
                               confirmation_id INT AUTO_INCREMENT PRIMARY KEY,
                               image_id INT,
                               user_id INT,
                               confirmation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               status ENUM('confirmed', 'rejected') NOT NULL,
                               FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE,
                               FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                               INDEX idx_confirmation_time (confirmation_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- tabla de calidad del aire
CREATE TABLE air_quality (
                             record_id INT AUTO_INCREMENT PRIMARY KEY,
                             measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             pm25 FLOAT NOT NULL,
                             pm10 FLOAT NOT NULL,
                             pm01 FLOAT NOT NULL,
                             INDEX idx_measurement_time (measurement_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

