-- =========================================================================
-- REPORTES (10 consultas, 9 de ellas con JOIN)
-- Proyecto: Asignación de Horarios y Carga Académica
-- Implementados como procedimientos almacenados para ser invocados
-- directamente desde el aplicativo (CALL sp_reporte_XX(...)).
-- =========================================================================
USE bd_horarios_esclavas;

DELIMITER $$

-- R1. Horario completo de una sección (JOIN: Seccion_Periodo + Actividad + Asignatura + Espacio + Seccion + Grado_Escolar)
DROP PROCEDURE IF EXISTS sp_reporte_01_horario_seccion $$
CREATE PROCEDURE sp_reporte_01_horario_seccion(IN p_id_seccion INT)
BEGIN
    SELECT a.Periodo, ge.Nombre AS Grado, ge.Nivel, s.Letra_Identificadora AS Seccion,
           a.Dia, a.Hora_Inicio, a.Hora_Fin, a.Naturaleza,
           COALESCE(a.Materia_Asignatura, '—') AS Asignatura, a.Espacio
      FROM Seccion_Periodo sp
      JOIN Actividad a ON a.ID_Actividad = sp.ID_Actividad
      JOIN Seccion s ON s.ID_Seccion = sp.ID_Seccion
      JOIN Grado_Escolar ge ON ge.ID_Grado = s.ID_Grado
     WHERE sp.ID_Seccion = p_id_seccion
     ORDER BY a.Periodo DESC, FIELD(a.Dia,'Lunes','Martes','Miércoles','Jueves','Viernes'), a.Hora_Inicio;
END $$

-- R2. Carga horaria semanal de un docente (JOIN: Docente_Actividad + Actividad + Docente)
DROP PROCEDURE IF EXISTS sp_reporte_02_carga_docente $$
CREATE PROCEDURE sp_reporte_02_carga_docente(IN p_dni CHAR(8))
BEGIN
    SELECT a.Periodo, d.Nombre AS Docente, a.Dia, a.Hora_Inicio, a.Hora_Fin,
           COALESCE(a.Materia_Asignatura,'—') AS Asignatura, da.Rol_Asumido, a.Espacio
      FROM Docente_Actividad da
      JOIN Actividad a ON a.ID_Actividad = da.ID_Actividad
      JOIN Docente d ON d.DNI = da.DNI_Docente
     WHERE da.DNI_Docente = p_dni
     ORDER BY a.Periodo DESC, FIELD(a.Dia,'Lunes','Martes','Miércoles','Jueves','Viernes'), a.Hora_Inicio;
END $$

-- R3. Docentes especializados en una asignatura (JOIN: Especializado_En + Docente + Asignatura)
DROP PROCEDURE IF EXISTS sp_reporte_03_docentes_por_asignatura $$
CREATE PROCEDURE sp_reporte_03_docentes_por_asignatura(IN p_materia VARCHAR(60))
BEGIN
    SELECT asg.Nombre_Materia AS Asignatura, d.Nombre AS Docente, d.Modalidad, d.Condicion_Especial
      FROM Especializado_En e
      JOIN Docente d ON d.DNI = e.DNI_Docente
      JOIN Asignatura asg ON asg.Nombre_Materia = e.Nombre_Asignatura
     WHERE e.Nombre_Asignatura = p_materia
     ORDER BY d.Nombre;
END $$

-- R4. Plan de estudios (horas exigidas) de un grado (JOIN: Grado_Materia + Asignatura + Grado_Escolar)
DROP PROCEDURE IF EXISTS sp_reporte_04_plan_estudios_grado $$
CREATE PROCEDURE sp_reporte_04_plan_estudios_grado(IN p_id_grado INT)
BEGIN
    SELECT ge.Nombre AS Grado, ge.Nivel, gm.Nombre_Asignatura AS Asignatura,
           asg.Nivel_Exigencia, gm.Horas_Exigidas
      FROM Grado_Materia gm
      JOIN Grado_Escolar ge ON ge.ID_Grado = gm.ID_Grado
      JOIN Asignatura asg ON asg.Nombre_Materia = gm.Nombre_Asignatura
     WHERE gm.ID_Grado = p_id_grado
     ORDER BY gm.Horas_Exigidas DESC;
END $$

-- R5. Ocupación de espacios en un día determinado (JOIN: Actividad + Espacio)
DROP PROCEDURE IF EXISTS sp_reporte_05_ocupacion_espacios $$
CREATE PROCEDURE sp_reporte_05_ocupacion_espacios(IN p_dia VARCHAR(10))
BEGIN
    SELECT e.Denominacion AS Espacio, e.Categoria, a.Hora_Inicio, a.Hora_Fin,
           a.Naturaleza, COALESCE(a.Materia_Asignatura,'—') AS Asignatura
      FROM Actividad a
      JOIN Espacio e ON e.Denominacion = a.Espacio
     WHERE a.Dia = p_dia
     ORDER BY e.Denominacion, a.Hora_Inicio;
END $$

-- R6. Actividades por naturaleza dentro de un periodo académico (JOIN: Actividad + Periodo_Academico)
DROP PROCEDURE IF EXISTS sp_reporte_06_actividades_por_naturaleza $$
CREATE PROCEDURE sp_reporte_06_actividades_por_naturaleza(IN p_naturaleza VARCHAR(30), IN p_anio SMALLINT)
BEGIN
    SELECT pa.Anio_Lectivo, pa.Estado, a.Dia, a.Hora_Inicio, a.Hora_Fin, a.Espacio
      FROM Actividad a
      JOIN Periodo_Academico pa ON pa.Anio_Lectivo = a.Periodo
     WHERE a.Naturaleza = p_naturaleza AND a.Periodo = p_anio
     ORDER BY FIELD(a.Dia,'Lunes','Martes','Miércoles','Jueves','Viernes'), a.Hora_Inicio;
END $$

-- R7. Docentes con condición especial y su carga de actividades (JOIN: Docente + Docente_Actividad + Actividad)
DROP PROCEDURE IF EXISTS sp_reporte_07_docentes_condicion_especial $$
CREATE PROCEDURE sp_reporte_07_docentes_condicion_especial()
BEGIN
    SELECT d.Nombre AS Docente, d.Condicion_Especial, COUNT(da.ID_Actividad) AS Total_Actividades
      FROM Docente d
      JOIN Docente_Actividad da ON da.DNI_Docente = d.DNI
      JOIN Actividad a ON a.ID_Actividad = da.ID_Actividad
     WHERE d.Condicion_Especial IS NOT NULL AND d.Condicion_Especial <> 'Docente'
     GROUP BY d.DNI, d.Nombre, d.Condicion_Especial
     ORDER BY Total_Actividades DESC;
END $$

-- R8. Secciones por nivel educativo (JOIN: Seccion + Grado_Escolar)
DROP PROCEDURE IF EXISTS sp_reporte_08_secciones_por_nivel $$
CREATE PROCEDURE sp_reporte_08_secciones_por_nivel(IN p_nivel VARCHAR(20))
BEGIN
    SELECT ge.Nombre AS Grado, ge.Nivel, s.ID_Seccion, s.Letra_Identificadora
      FROM Seccion s
      JOIN Grado_Escolar ge ON ge.ID_Grado = s.ID_Grado
     WHERE ge.Nivel = p_nivel
     ORDER BY ge.ID_Grado, s.Letra_Identificadora;
END $$

-- R9. Horas exigidas (plan de estudios x secciones) vs. bloques de clase realmente programados
--     (JOIN: Asignatura + Grado_Materia + Seccion + Actividad + Seccion_Periodo).
--     Cada lado se agrega en su propia subconsulta para no multiplicar filas.
DROP PROCEDURE IF EXISTS sp_reporte_09_horas_exigidas_vs_programadas $$
CREATE PROCEDURE sp_reporte_09_horas_exigidas_vs_programadas(IN p_anio SMALLINT)
BEGIN
    SELECT asg.Nombre_Materia AS Asignatura,
           COALESCE(pl.Horas, 0) AS Horas_Exigidas_Plan_Estudios,
           COALESCE(pr.Bloques, 0) AS Bloques_Programados,
           COALESCE(pr.Bloques, 0) - COALESCE(pl.Horas, 0) AS Diferencia
      FROM Asignatura asg
      LEFT JOIN (SELECT gm.Nombre_Asignatura, SUM(gm.Horas_Exigidas) AS Horas
                   FROM Grado_Materia gm
                   JOIN Seccion s ON s.ID_Grado = gm.ID_Grado
                  GROUP BY gm.Nombre_Asignatura) pl ON pl.Nombre_Asignatura = asg.Nombre_Materia
      LEFT JOIN (SELECT a.Materia_Asignatura, COUNT(*) AS Bloques
                   FROM Actividad a
                   JOIN Seccion_Periodo sp ON sp.ID_Actividad = a.ID_Actividad
                  WHERE a.Periodo = p_anio AND a.Naturaleza = 'Clase'
                  GROUP BY a.Materia_Asignatura) pr ON pr.Materia_Asignatura = asg.Nombre_Materia
     ORDER BY Horas_Exigidas_Plan_Estudios DESC, Asignatura;
END $$

-- R10. Bitácora de los últimos cambios registrados (sin JOIN; auditoría)
DROP PROCEDURE IF EXISTS sp_reporte_10_bitacora_reciente $$
CREATE PROCEDURE sp_reporte_10_bitacora_reciente(IN p_limite INT)
BEGIN
    SELECT Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Fecha_Hora, Detalle
      FROM Bitacora
     ORDER BY Fecha_Hora DESC
     LIMIT p_limite;
END $$

DELIMITER ;
