-- =========================================================================
-- PROCEDIMIENTOS ALMACENADOS CRUD
-- Proyecto: Asignación de Horarios y Carga Académica
-- Uno de inserción, uno de modificación y uno de borrado por cada una
-- de las 11 tablas del modelo físico.
-- =========================================================================
USE bd_horarios_esclavas;

DELIMITER $$

-- -------------------------------------------------------------------------
-- 1. GRADO_ESCOLAR
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_grado_escolar $$
CREATE PROCEDURE sp_insertar_grado_escolar(
    IN p_id_grado INT, IN p_nombre VARCHAR(30), IN p_nivel VARCHAR(20)
)
BEGIN
    INSERT INTO Grado_Escolar (ID_Grado, Nombre, Nivel) VALUES (p_id_grado, p_nombre, p_nivel);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_grado_escolar $$
CREATE PROCEDURE sp_modificar_grado_escolar(
    IN p_id_grado INT, IN p_nombre VARCHAR(30), IN p_nivel VARCHAR(20)
)
BEGIN
    UPDATE Grado_Escolar SET Nombre = p_nombre, Nivel = p_nivel WHERE ID_Grado = p_id_grado;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_grado_escolar $$
CREATE PROCEDURE sp_eliminar_grado_escolar(IN p_id_grado INT)
BEGIN
    DELETE FROM Grado_Escolar WHERE ID_Grado = p_id_grado;
END $$

-- -------------------------------------------------------------------------
-- 2. DOCENTE
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_docente $$
CREATE PROCEDURE sp_insertar_docente(
    IN p_dni CHAR(8), IN p_nombre VARCHAR(100), IN p_modalidad VARCHAR(25), IN p_condicion VARCHAR(50)
)
BEGIN
    INSERT INTO Docente (DNI, Nombre, Modalidad, Condicion_Especial)
    VALUES (p_dni, p_nombre, p_modalidad, p_condicion);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_docente $$
CREATE PROCEDURE sp_modificar_docente(
    IN p_dni CHAR(8), IN p_nombre VARCHAR(100), IN p_modalidad VARCHAR(25), IN p_condicion VARCHAR(50)
)
BEGIN
    UPDATE Docente
       SET Nombre = p_nombre, Modalidad = p_modalidad, Condicion_Especial = p_condicion
     WHERE DNI = p_dni;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_docente $$
CREATE PROCEDURE sp_eliminar_docente(IN p_dni CHAR(8))
BEGIN
    DELETE FROM Docente WHERE DNI = p_dni;
END $$

-- -------------------------------------------------------------------------
-- 3. ASIGNATURA
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_asignatura $$
CREATE PROCEDURE sp_insertar_asignatura(
    IN p_nombre_materia VARCHAR(60), IN p_nivel_exigencia VARCHAR(30)
)
BEGIN
    INSERT INTO Asignatura (Nombre_Materia, Nivel_Exigencia) VALUES (p_nombre_materia, p_nivel_exigencia);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_asignatura $$
CREATE PROCEDURE sp_modificar_asignatura(
    IN p_nombre_materia VARCHAR(60), IN p_nivel_exigencia VARCHAR(30)
)
BEGIN
    UPDATE Asignatura SET Nivel_Exigencia = p_nivel_exigencia WHERE Nombre_Materia = p_nombre_materia;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_asignatura $$
CREATE PROCEDURE sp_eliminar_asignatura(IN p_nombre_materia VARCHAR(60))
BEGIN
    DELETE FROM Asignatura WHERE Nombre_Materia = p_nombre_materia;
END $$

-- -------------------------------------------------------------------------
-- 4. PERIODO_ACADEMICO
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_periodo $$
CREATE PROCEDURE sp_insertar_periodo(IN p_anio SMALLINT, IN p_estado VARCHAR(10))
BEGIN
    INSERT INTO Periodo_Academico (Anio_Lectivo, Estado) VALUES (p_anio, p_estado);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_periodo $$
CREATE PROCEDURE sp_modificar_periodo(IN p_anio SMALLINT, IN p_estado VARCHAR(10))
BEGIN
    UPDATE Periodo_Academico SET Estado = p_estado WHERE Anio_Lectivo = p_anio;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_periodo $$
CREATE PROCEDURE sp_eliminar_periodo(IN p_anio SMALLINT)
BEGIN
    DELETE FROM Periodo_Academico WHERE Anio_Lectivo = p_anio;
END $$

-- -------------------------------------------------------------------------
-- 5. SECCION
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_seccion $$
CREATE PROCEDURE sp_insertar_seccion(
    IN p_id_seccion INT, IN p_letra VARCHAR(2), IN p_id_grado INT
)
BEGIN
    INSERT INTO Seccion (ID_Seccion, Letra_Identificadora, ID_Grado)
    VALUES (p_id_seccion, p_letra, p_id_grado);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_seccion $$
CREATE PROCEDURE sp_modificar_seccion(
    IN p_id_seccion INT, IN p_letra VARCHAR(2), IN p_id_grado INT
)
BEGIN
    UPDATE Seccion SET Letra_Identificadora = p_letra, ID_Grado = p_id_grado WHERE ID_Seccion = p_id_seccion;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_seccion $$
CREATE PROCEDURE sp_eliminar_seccion(IN p_id_seccion INT)
BEGIN
    DELETE FROM Seccion WHERE ID_Seccion = p_id_seccion;
END $$

-- -------------------------------------------------------------------------
-- 6. ESPACIO
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_espacio $$
CREATE PROCEDURE sp_insertar_espacio(
    IN p_denominacion VARCHAR(60), IN p_categoria VARCHAR(30), IN p_limite SMALLINT
)
BEGIN
    INSERT INTO Espacio (Denominacion, Categoria, Limite_Grupos) VALUES (p_denominacion, p_categoria, p_limite);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_espacio $$
CREATE PROCEDURE sp_modificar_espacio(
    IN p_denominacion VARCHAR(60), IN p_categoria VARCHAR(30), IN p_limite SMALLINT
)
BEGIN
    UPDATE Espacio SET Categoria = p_categoria, Limite_Grupos = p_limite WHERE Denominacion = p_denominacion;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_espacio $$
CREATE PROCEDURE sp_eliminar_espacio(IN p_denominacion VARCHAR(60))
BEGIN
    DELETE FROM Espacio WHERE Denominacion = p_denominacion;
END $$

-- -------------------------------------------------------------------------
-- 7. ACTIVIDAD (núcleo transaccional; la validación de cruces la hace el
--    trigger trg_actividad_bi / trg_actividad_bu, ver 03_triggers.sql)
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_actividad $$
CREATE PROCEDURE sp_insertar_actividad(
    IN p_id INT, IN p_hora_inicio TIME, IN p_hora_fin TIME, IN p_dia VARCHAR(10),
    IN p_naturaleza VARCHAR(30), IN p_materia VARCHAR(60), IN p_periodo SMALLINT, IN p_espacio VARCHAR(60)
)
BEGIN
    INSERT INTO Actividad (ID_Actividad, Hora_Inicio, Hora_Fin, Dia, Naturaleza, Materia_Asignatura, Periodo, Espacio)
    VALUES (p_id, p_hora_inicio, p_hora_fin, p_dia, p_naturaleza, p_materia, p_periodo, p_espacio);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_actividad $$
CREATE PROCEDURE sp_modificar_actividad(
    IN p_id INT, IN p_hora_inicio TIME, IN p_hora_fin TIME, IN p_dia VARCHAR(10),
    IN p_naturaleza VARCHAR(30), IN p_materia VARCHAR(60), IN p_periodo SMALLINT, IN p_espacio VARCHAR(60)
)
BEGIN
    UPDATE Actividad
       SET Hora_Inicio = p_hora_inicio, Hora_Fin = p_hora_fin, Dia = p_dia,
           Naturaleza = p_naturaleza, Materia_Asignatura = p_materia,
           Periodo = p_periodo, Espacio = p_espacio
     WHERE ID_Actividad = p_id;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_actividad $$
CREATE PROCEDURE sp_eliminar_actividad(IN p_id INT)
BEGIN
    DELETE FROM Actividad WHERE ID_Actividad = p_id;
END $$

-- -------------------------------------------------------------------------
-- 8. GRADO_MATERIA
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_grado_materia $$
CREATE PROCEDURE sp_insertar_grado_materia(
    IN p_nombre_asignatura VARCHAR(60), IN p_id_grado INT, IN p_horas SMALLINT
)
BEGIN
    INSERT INTO Grado_Materia (Nombre_Asignatura, ID_Grado, Horas_Exigidas)
    VALUES (p_nombre_asignatura, p_id_grado, p_horas);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_grado_materia $$
CREATE PROCEDURE sp_modificar_grado_materia(
    IN p_nombre_asignatura VARCHAR(60), IN p_id_grado INT, IN p_horas SMALLINT
)
BEGIN
    UPDATE Grado_Materia SET Horas_Exigidas = p_horas
     WHERE Nombre_Asignatura = p_nombre_asignatura AND ID_Grado = p_id_grado;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_grado_materia $$
CREATE PROCEDURE sp_eliminar_grado_materia(IN p_nombre_asignatura VARCHAR(60), IN p_id_grado INT)
BEGIN
    DELETE FROM Grado_Materia WHERE Nombre_Asignatura = p_nombre_asignatura AND ID_Grado = p_id_grado;
END $$

-- -------------------------------------------------------------------------
-- 9. ESPECIALIZADO_EN
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_especializado_en $$
CREATE PROCEDURE sp_insertar_especializado_en(IN p_nombre_asignatura VARCHAR(60), IN p_dni CHAR(8))
BEGIN
    INSERT INTO Especializado_En (Nombre_Asignatura, DNI_Docente) VALUES (p_nombre_asignatura, p_dni);
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_especializado_en $$
CREATE PROCEDURE sp_eliminar_especializado_en(IN p_nombre_asignatura VARCHAR(60), IN p_dni CHAR(8))
BEGIN
    DELETE FROM Especializado_En WHERE Nombre_Asignatura = p_nombre_asignatura AND DNI_Docente = p_dni;
END $$
-- (Especializado_En no tiene atributos propios además de la PK compuesta,
--  por lo que "modificar" no aplica: se elimina y se vuelve a insertar.)

-- -------------------------------------------------------------------------
-- 10. SECCION_PERIODO (relación INVOLUCRA: Sección participa en Actividad)
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_seccion_periodo $$
CREATE PROCEDURE sp_insertar_seccion_periodo(IN p_id_actividad INT, IN p_id_seccion INT)
BEGIN
    INSERT INTO Seccion_Periodo (ID_Actividad, ID_Seccion) VALUES (p_id_actividad, p_id_seccion);
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_seccion_periodo $$
CREATE PROCEDURE sp_eliminar_seccion_periodo(IN p_id_actividad INT, IN p_id_seccion INT)
BEGIN
    DELETE FROM Seccion_Periodo WHERE ID_Actividad = p_id_actividad AND ID_Seccion = p_id_seccion;
END $$

-- -------------------------------------------------------------------------
-- 11. DOCENTE_ACTIVIDAD
-- -------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_insertar_docente_actividad $$
CREATE PROCEDURE sp_insertar_docente_actividad(
    IN p_dni CHAR(8), IN p_id_actividad INT, IN p_rol VARCHAR(40)
)
BEGIN
    INSERT INTO Docente_Actividad (DNI_Docente, ID_Actividad, Rol_Asumido)
    VALUES (p_dni, p_id_actividad, p_rol);
END $$

DROP PROCEDURE IF EXISTS sp_modificar_docente_actividad $$
CREATE PROCEDURE sp_modificar_docente_actividad(
    IN p_dni CHAR(8), IN p_id_actividad INT, IN p_rol VARCHAR(40)
)
BEGIN
    UPDATE Docente_Actividad SET Rol_Asumido = p_rol
     WHERE DNI_Docente = p_dni AND ID_Actividad = p_id_actividad;
END $$

DROP PROCEDURE IF EXISTS sp_eliminar_docente_actividad $$
CREATE PROCEDURE sp_eliminar_docente_actividad(IN p_dni CHAR(8), IN p_id_actividad INT)
BEGIN
    DELETE FROM Docente_Actividad WHERE DNI_Docente = p_dni AND ID_Actividad = p_id_actividad;
END $$

DELIMITER ;
