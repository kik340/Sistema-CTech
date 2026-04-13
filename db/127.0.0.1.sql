CREATE DATABASE IF NOT EXISTS itsa_qr;
USE itsa_qr;

DROP TABLE IF EXISTS seguimiento_detalle;
DROP TABLE IF EXISTS seguimiento_academico;
DROP TABLE IF EXISTS asistencias_tutoria;
DROP TABLE IF EXISTS alumnos_grupo;
DROP TABLE IF EXISTS grupos;
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
    carrera_id INT NOT NULL,
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
    password VARCHAR(255) NOT NULL,
    tipo ENUM('tutor','laboratorista') NOT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

CREATE TABLE grupos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carrera_id INT NOT NULL,
    semestre VARCHAR(20) NOT NULL,
    grupo VARCHAR(20) NOT NULL,
    turno VARCHAR(20) DEFAULT NULL,
    periodo VARCHAR(30) DEFAULT NULL,
    tutor_matricula VARCHAR(20) DEFAULT NULL,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
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

    comentario TEXT DEFAULT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_seguimiento_alumno (seguimiento_id, alumno_matricula),
    FOREIGN KEY (seguimiento_id) REFERENCES seguimiento_academico(id)
);

CREATE TABLE asistencias_tutoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL,
    parcial ENUM('1','2','3','4') NOT NULL,
    alumno_matricula VARCHAR(20) NOT NULL,
    nombre_alumno VARCHAR(180) NOT NULL,
    asistencia_grupal TINYINT(1) DEFAULT 0,
    asistencia_individual TINYINT(1) DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_asistencia_parcial_alumno (grupo_id, parcial, alumno_matricula),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id)
);
CREATE TABLE materias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carrera_id INT NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    semestre VARCHAR(20) NOT NULL,
    activa TINYINT(1) DEFAULT 1,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);
INSERT INTO personal
(
    matricula,
    nombre,
    ap_paterno,
    ap_materno,
    nombre_completo,
    email,
    password,
    tipo,
    activo
)
VALUES
(
    'TT260101',
    'Admin',
    'General',
    'ITSA',
    'Admin General ITSA',
    'II260101@itsatlixco.edu.mx',
    'scrypt:32768:8:1$ItlaoEZG61AwbYit$a2c0dd346c2dab14f6decf61fb9d8010d389eec6b9fe0e89db12b53c1fb2beda17da2f2bf48dccfd233b32a5c044f424baffd3f4fed3487fdc5d9262b7e6307d',
    'tutor',
    1
);
INSERT INTO alumnos 
(matricula, nombre, ap_paterno, ap_materno, nombre_completo, email, password, carrera_id, anio_ingreso, activo)
VALUES
(
'II231843',
'Carlos Alberto',
'Gallardo',
'Moreno',
'Carlos Alberto Gallardo Moreno',
'II231843@itsatlixco.edu.mx',
'scrypt:32768:8:1$E29ZGHnrdzgTFoXZ$d82d946ffc18666739ecbbe31b7a13e1989cd6ecd72ce9953fcc2ef2f89cd2255894ef9e8062f4fd3e307be224e48a94a6d2bbde71c9df1f2710d59ab647cd35',
18,
2023,
1
);

INSERT INTO alumnos 
(matricula, nombre, ap_paterno, ap_materno, nombre_completo, email, password, carrera_id, anio_ingreso, activo)
VALUES
(
'II231807',
'Dulce María',
'González',
'Ramírez',
'Dulce María González Ramírez',
'II231807@itsatlixco.edu.mx',
'scrypt:32768:8:1$E29ZGHnrdzgTFoXZ$d82d946ffc18666739ecbbe31b7a13e1989cd6ecd72ce9953fcc2ef2f89cd2255894ef9e8062f4fd3e307be224e48a94a6d2bbde71c9df1f2710d59ab647cd35',
18,
2023,
1
);

INSERT INTO alumnos 
(matricula, nombre, ap_paterno, ap_materno, nombre_completo, email, password, carrera_id, anio_ingreso, activo)
VALUES
(
'II231870',
'María Isabel',
'Ramos',
'Morales',
'María Isabel Ramos Morales',
'II231870@itsatlixco.edu.mx',
'scrypt:32768:8:1$E29ZGHnrdzgTFoXZ$d82d946ffc18666739ecbbe31b7a13e1989cd6ecd72ce9953fcc2ef2f89cd2255894ef9e8062f4fd3e307be224e48a94a6d2bbde71c9df1f2710d59ab647cd35',
18,
2023,
1
);

INSERT INTO alumnos 
(matricula, nombre, ap_paterno, ap_materno, nombre_completo, email, password, carrera_id, anio_ingreso, activo)
VALUES
(
'II231841',
'Lesly',
'Zenteno',
'Morales',
'Lesly Zenteno Morales',
'II231841@itsatlixco.edu.mx',
'scrypt:32768:8:1$E29ZGHnrdzgTFoXZ$d82d946ffc18666739ecbbe31b7a13e1989cd6ecd72ce9953fcc2ef2f89cd2255894ef9e8062f4fd3e307be224e48a94a6d2bbde71c9df1f2710d59ab647cd35',
18,
2023,
1
);

INSERT INTO alumnos 
(matricula, nombre, ap_paterno, ap_materno, nombre_completo, email, password, carrera_id, anio_ingreso, activo)
VALUES
(
'II231839',
'Allison',
'Caltitla',
'Axilote',
'Allison Caltitla Axilote',
'II231839@itsatlixco.edu.mx',
'scrypt:32768:8:1$E29ZGHnrdzgTFoXZ$d82d946ffc18666739ecbbe31b7a13e1989cd6ecd72ce9953fcc2ef2f89cd2255894ef9e8062f4fd3e307be224e48a94a6d2bbde71c9df1f2710d59ab647cd35',
18,
2023,
1
);
ALTER TABLE personal
ADD COLUMN carrera_id INT DEFAULT NULL,
ADD CONSTRAINT fk_personal_carrera
FOREIGN KEY (carrera_id) REFERENCES carreras(id);

ALTER TABLE grupos
ADD COLUMN materia_id INT NOT NULL,
ADD CONSTRAINT fk_grupos_materia
FOREIGN KEY (materia_id) REFERENCES materias(id);

ALTER TABLE grupos
MODIFY tutor_matricula VARCHAR(20) NULL;

ALTER TABLE personal
ADD COLUMN correo_temporal VARCHAR(150) NULL AFTER email;

ALTER TABLE alumnos
ADD COLUMN anio_ingreso SMALLINT NOT NULL AFTER carrera_id;

ALTER TABLE solicitudes_registro
ADD COLUMN anio_ingreso SMALLINT NULL AFTER carrera_id;

INSERT INTO carreras (id, nombre, activa)
SELECT 18, 'Ingeniería Industrial', 1
WHERE NOT EXISTS (
    SELECT 1
    FROM carreras
    WHERE id = 18 OR nombre = 'Ingeniería Industrial'
);

ALTER TABLE carreras AUTO_INCREMENT = 19;