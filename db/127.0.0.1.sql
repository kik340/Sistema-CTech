
CREATE DATABASE IF NOT EXISTS buap_proysoft;
USE buap_proysoft;

DROP TABLE IF EXISTS seguimiento_detalle;
DROP TABLE IF EXISTS seguimiento_academico;
DROP TABLE IF EXISTS asistencias_tutoria;
DROP TABLE IF EXISTS alumnos_grupo;
DROP TABLE IF EXISTS grupos;
DROP TABLE IF EXISTS materias;
DROP TABLE IF EXISTS prestamos_equipo;
DROP TABLE IF EXISTS equipos_laboratorio;
DROP TABLE IF EXISTS solicitudes_registro;
DROP TABLE IF EXISTS alumnos;
DROP TABLE IF EXISTS externos;
DROP TABLE IF EXISTS personal;
DROP TABLE IF EXISTS carreras;

CREATE TABLE carreras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    activa TINYINT(1) DEFAULT 1
);

CREATE TABLE alumnos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(60) NOT NULL,
    ap_paterno VARCHAR(60) NOT NULL,
    ap_materno VARCHAR(60) NOT NULL,
    nombre_completo VARCHAR(180) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    genero VARCHAR(2) NOT NULL,
    carrera_id INT NOT NULL,
    anio_ingreso SMALLINT NOT NULL,
    foto VARCHAR(255) DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);

CREATE TABLE externos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(60) NOT NULL,
    ap_paterno VARCHAR(60) NOT NULL,
    ap_materno VARCHAR(60) NOT NULL,
    nombre_completo VARCHAR(180) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    motivo VARCHAR(255) DEFAULT NULL,
    qr_temporal TINYINT(1) DEFAULT 1,
    fecha_expiracion DATETIME DEFAULT NULL,
    foto VARCHAR(255) DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(60) NOT NULL,
    ap_paterno VARCHAR(60) NOT NULL,
    ap_materno VARCHAR(60) NOT NULL,
    nombre_completo VARCHAR(180) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    correo_temporal VARCHAR(150) NULL,
    password VARCHAR(255) NOT NULL,
    tipo ENUM('tutor','laboratorista') NOT NULL,
    carrera_id INT DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);

CREATE TABLE solicitudes_registro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    ap_paterno VARCHAR(60) NOT NULL,
    ap_materno VARCHAR(60) NOT NULL,
    nombre_completo VARCHAR(180) NOT NULL,
    correo_temporal VARCHAR(150) NOT NULL,
    password VARCHAR(255) NOT NULL,
    tipo_solicitud ENUM('alumno','externo') NOT NULL DEFAULT 'alumno',
    carrera_id INT DEFAULT NULL,
    anio_ingreso SMALLINT NULL,
    motivo VARCHAR(255) DEFAULT NULL,
    estado ENUM('pendiente','aprobada','rechazada') DEFAULT 'pendiente',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);

CREATE TABLE equipos_laboratorio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_equipo VARCHAR(30) NOT NULL UNIQUE,
    nombre_equipo VARCHAR(100) NOT NULL,
    categoria VARCHAR(80) NOT NULL,
    marca VARCHAR(80) DEFAULT NULL,
    modelo VARCHAR(80) DEFAULT NULL,
    numero_serie VARCHAR(100) DEFAULT NULL UNIQUE,
    descripcion TEXT DEFAULT NULL,
    estado ENUM('disponible','prestado','mantenimiento','baja') DEFAULT 'disponible',
    ubicacion VARCHAR(120) DEFAULT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prestamos_equipo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipo_id INT NOT NULL,
    matricula_usuario VARCHAR(20) NOT NULL,
    tipo_usuario ENUM('alumno','externo','tutor','laboratorista') NOT NULL,
    fecha_prestamo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_limite DATETIME DEFAULT NULL,
    fecha_devolucion DATETIME DEFAULT NULL,
    estado ENUM('activo','devuelto','vencido','cancelado') DEFAULT 'activo',
    observaciones TEXT DEFAULT NULL,
    FOREIGN KEY (equipo_id) REFERENCES equipos_laboratorio(id)
);

CREATE TABLE materias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carrera_id INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    semestre VARCHAR(20) NOT NULL,
    activa TINYINT(1) DEFAULT 1,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);

CREATE TABLE grupos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carrera_id INT NOT NULL,
    materia_id INT NOT NULL,
    semestre VARCHAR(20) NOT NULL,
    grupo VARCHAR(20) NOT NULL,
    turno VARCHAR(20) DEFAULT NULL,
    periodo VARCHAR(30) DEFAULT NULL,
    tutor_matricula VARCHAR(20) DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id),
    FOREIGN KEY (materia_id) REFERENCES materias(id)
);

CREATE TABLE alumnos_grupo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumno_matricula VARCHAR(20) NOT NULL,
    grupo_id INT NOT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_alumno_grupo (alumno_matricula, grupo_id),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id)
);

CREATE TABLE seguimiento_academico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    tutor_matricula VARCHAR(20) DEFAULT NULL,
    parcial ENUM('1','2','3','4','S') NOT NULL,
    total_estudiantes INT NOT NULL DEFAULT 0,
    observaciones TEXT DEFAULT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_grupo_parcial (grupo_id, parcial),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id)
);

CREATE TABLE seguimiento_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seguimiento_id INT NOT NULL,
    alumno_matricula VARCHAR(20) NOT NULL,
    asistencia TINYINT(1) DEFAULT 0,
    canalizacion_tutoria_individual TINYINT(1) DEFAULT 0,
    problemas_economicos TINYINT(1) DEFAULT 0,
    problemas_salud TINYINT(1) DEFAULT 0,
    problemas_emocionales TINYINT(1) DEFAULT 0,
    problemas_familiares TINYINT(1) DEFAULT 0,
    problemas_academicos TINYINT(1) DEFAULT 0,
    beca_jcf TINYINT(1) DEFAULT 0,
    beca_manutencion TINYINT(1) DEFAULT 0,
    beca_jmf TINYINT(1) DEFAULT 0,
    beca_otro TINYINT(1) DEFAULT 0,
    apoyo_psicologico TINYINT(1) DEFAULT 0,
    apoyo_medico TINYINT(1) DEFAULT 0,
    apoyo_otro TINYINT(1) DEFAULT 0,
    promedio DECIMAL(5,2) DEFAULT NULL,
    materias_reprobadas INT DEFAULT 0,
    estatus_aprobado TINYINT(1) DEFAULT 0,
    posible_desercion TINYINT(1) DEFAULT 0,
    entrego_actividad TINYINT(1) DEFAULT 0,
    comentario TEXT DEFAULT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_seguimiento_alumno (seguimiento_id, alumno_matricula),
    FOREIGN KEY (seguimiento_id) REFERENCES seguimiento_academico(id)
);

CREATE TABLE sesiones_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_actual VARCHAR(100) NOT NULL,
    token_anterior VARCHAR(100) DEFAULT NULL,
    grupo_id INT NOT NULL,
    tutor_matricula VARCHAR(20) NOT NULL,
    fecha_inicio DATETIME NOT NULL,
    fecha_expiracion DATETIME NOT NULL,
    usado TINYINT(1) DEFAULT 0,
    activa TINYINT(1) DEFAULT 1,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id)
);

-- Asistencias registradas (una por alumno por sesión)
CREATE TABLE asistencias_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    sesion_id INT NOT NULL,
    alumno_matricula VARCHAR(20) NOT NULL,
    fecha_asistencia DATETIME NOT NULL,
    UNIQUE KEY uk_alumno_sesion (sesion_id, alumno_matricula),
    FOREIGN KEY (sesion_id) REFERENCES sesiones_tutoria(id)
);

CREATE TABLE IF NOT EXISTS actividades_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    parcial VARCHAR(2) NOT NULL,
    sesion_num INT NOT NULL,  -- 1 a 4 por parcial
    nombre_actividad VARCHAR(255) NOT NULL,
    descripcion TEXT,
    evidencia_path VARCHAR(500),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id),
    UNIQUE KEY uk_grupo_parcial_sesion (grupo_id, parcial, sesion_num)
);


ALTER TABLE sesiones_tutoria ADD COLUMN IF NOT EXISTS parcial VARCHAR(2) DEFAULT '1';
ALTER TABLE asistencias_tutoria ADD COLUMN IF NOT EXISTS nombre_alumno VARCHAR(180) DEFAULT '';

-- 1. Insertar la carrera Ingeniería en Ciberseguridad con ID = 1
INSERT INTO carreras (id, nombre, activa) 
VALUES (1, 'Ingeniería en Ciberseguridad', 1)
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre), activa = VALUES(activa);

-- 2. Insertar los alumnos en la tabla 'alumnos'
INSERT INTO alumnos (
    matricula, 
    nombre, 
    ap_paterno, 
    ap_materno, 
    nombre_completo, 
    email, 
    password, 
    genero, 
    carrera_id, 
    anio_ingreso, 
    activo
) VALUES 
(
    '202442654', 
    'Gustavo', 
    'Flores', 
    'Aguilar', 
    'Gustavo Flores Aguilar', 
    'fa202442654@alm.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'H', 
    1, 
    2024, 
    1
),
(
    '202438968', 
    'Jesús', 
    'Neria', 
    'Gómez', 
    'Jesús Neria Gómez', 
    'ng202438968@alm.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'H', 
    1, 
    2024, 
    1
),
(
    '202442606', 
    'Gonzalo', 
    'Fernandez', 
    'Rendón', 
    'Gonzalo Fernandez Rendón', 
    'fr202442606@alm.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'H', 
    1, 
    2024, 
    1
),
(
    '202433859', 
    'Luis Enrique', 
    'Encizo', 
    'Zea', 
    'Luis Enrique Encizo Zea', 
    'ez202433859@alm.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'H', 
    1, 
    2024, 
    1
),
(
    '202438708', 
    'Eduar Alejandro', 
    'Moreno', 
    'Ramos', 
    'Eduar Alejandro Moreno Ramos', 
    'mr202438708@alm.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'H', 
    1, 
    2024, 
    1
);

-- 3. Insertar la profesora en la tabla 'personal' (Tipo: tutor)
INSERT INTO personal (
    matricula, 
    nombre, 
    ap_paterno, 
    ap_materno, 
    nombre_completo, 
    email, 
    password, 
    tipo, 
    carrera_id, 
    activo
) VALUES (
    '100000001', 
    'Patricia Silvia', 
    'Sanchez', 
    '', 
    'Patricia Silvia Sanchez', 
    'ss100000001@correo.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'tutor', 
    1, 
    1
);

-- 4. Insertar el Laboratorista General BUAP en 'personal' (Tipo: laboratorista)
INSERT INTO personal (
    matricula, 
    nombre, 
    ap_paterno, 
    ap_materno, 
    nombre_completo, 
    email, 
    password, 
    tipo, 
    carrera_id, 
    activo
) VALUES (
    'LB1000001', 
    'Laboratorista', 
    'General', 
    'BUAP', 
    'Laboratorista General BUAP', 
    'gb1000001@correo.buap.mx', 
    'scrypt:32768:8:1$cBEO503AEonOXXyX$49009607bed6c16296092ec96faee2a376eb860d41b3296a529bd9c96c23b739bfcf99b7479d6c0b39eadb2510bdbee38cef1b75d28a9d55476e84eae1ee7146', 
    'laboratorista', 
    1, 
    1
);