-- =========================================================================
-- TRIGGERS
-- Proyecto: Asignación de Horarios y Carga Académica
-- 1) Bitácora de auditoría (quién/qué/cuándo se insertó, modificó o eliminó)
-- 2) Validación automática de cruces de horario (espacio y docente), como
--    refuerzo de la regla de negocio identificada desde la Entrega 1:
--    "el software solo impide el cruce de un mismo docente consigo mismo,
--     pero no impide que dos docentes sean asignados al mismo ambiente"
--    — aquí sí lo impedimos, a nivel de base de datos.
-- =========================================================================
USE bd_horarios_esclavas;

-- -------------------------------------------------------------------------
-- Tabla de Bitácora
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Bitacora (
    ID_Bitacora INT AUTO_INCREMENT PRIMARY KEY,
    Tabla_Afectada VARCHAR(40) NOT NULL,
    Operacion VARCHAR(10) NOT NULL COMMENT 'INSERT, UPDATE o DELETE',
    Registro_Afectado VARCHAR(120) NOT NULL COMMENT 'Clave primaria del registro afectado',
    Usuario VARCHAR(100) NOT NULL,
    Fecha_Hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Detalle VARCHAR(255) NULL
) ENGINE=InnoDB COMMENT='Auditoría de cambios realizados por el aplicativo';

DELIMITER $$

-- -------------------------------------------------------------------------
-- TRIGGERS DE VALIDACIÓN DE CRUCES — ACTIVIDAD
-- Evita que se programen dos actividades en el mismo espacio, día y periodo
-- con horarios que se solapan (no solo que coincidan exactamente).
-- -------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_actividad_cruce_bi $$
CREATE TRIGGER trg_actividad_cruce_bi
BEFORE INSERT ON Actividad
FOR EACH ROW
BEGIN
    DECLARE v_conflictos INT;
    SELECT COUNT(*) INTO v_conflictos
      FROM Actividad
     WHERE Espacio = NEW.Espacio
       AND Dia = NEW.Dia
       AND Periodo = NEW.Periodo
       AND NEW.Hora_Inicio < Hora_Fin
       AND NEW.Hora_Fin > Hora_Inicio;

    IF v_conflictos > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cruce de horario: el espacio ya está ocupado en ese día y rango de horas.';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_actividad_cruce_bu $$
CREATE TRIGGER trg_actividad_cruce_bu
BEFORE UPDATE ON Actividad
FOR EACH ROW
BEGIN
    DECLARE v_conflictos INT;
    SELECT COUNT(*) INTO v_conflictos
      FROM Actividad
     WHERE Espacio = NEW.Espacio
       AND Dia = NEW.Dia
       AND Periodo = NEW.Periodo
       AND ID_Actividad <> OLD.ID_Actividad
       AND NEW.Hora_Inicio < Hora_Fin
       AND NEW.Hora_Fin > Hora_Inicio;

    IF v_conflictos > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cruce de horario: el espacio ya está ocupado en ese día y rango de horas.';
    END IF;
END $$

-- -------------------------------------------------------------------------
-- TRIGGERS DE VALIDACIÓN DE CRUCES — DOCENTE_ACTIVIDAD
-- Evita que un mismo docente quede asignado a dos actividades que se
-- solapan en horario dentro del mismo periodo académico.
-- -------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_docente_actividad_cruce_bi $$
CREATE TRIGGER trg_docente_actividad_cruce_bi
BEFORE INSERT ON Docente_Actividad
FOR EACH ROW
BEGIN
    DECLARE v_conflictos INT;
    SELECT COUNT(*) INTO v_conflictos
      FROM Docente_Actividad da
      JOIN Actividad a1 ON a1.ID_Actividad = da.ID_Actividad
      JOIN Actividad a2 ON a2.ID_Actividad = NEW.ID_Actividad
     WHERE da.DNI_Docente = NEW.DNI_Docente
       AND a1.Dia = a2.Dia
       AND a1.Periodo = a2.Periodo
       AND a2.Hora_Inicio < a1.Hora_Fin
       AND a2.Hora_Fin > a1.Hora_Inicio;

    IF v_conflictos > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cruce de horario: el docente ya tiene otra actividad en ese día y rango de horas.';
    END IF;
END $$

-- -------------------------------------------------------------------------
-- TRIGGERS DE AUDITORÍA (Bitácora)
-- Registran automáticamente cada inserción, modificación y borrado
-- realizado sobre las tablas más sensibles del sistema.
-- -------------------------------------------------------------------------

-- ACTIVIDAD
DROP TRIGGER IF EXISTS trg_actividad_ai $$
CREATE TRIGGER trg_actividad_ai AFTER INSERT ON Actividad FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Actividad', 'INSERT', NEW.ID_Actividad, CURRENT_USER(),
            CONCAT('Dia=', NEW.Dia, ' Hora=', NEW.Hora_Inicio, '-', NEW.Hora_Fin, ' Espacio=', NEW.Espacio));
END $$

DROP TRIGGER IF EXISTS trg_actividad_au $$
CREATE TRIGGER trg_actividad_au AFTER UPDATE ON Actividad FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Actividad', 'UPDATE', NEW.ID_Actividad, CURRENT_USER(),
            CONCAT('Nuevo horario: ', NEW.Dia, ' ', NEW.Hora_Inicio, '-', NEW.Hora_Fin, ' Espacio=', NEW.Espacio));
END $$

DROP TRIGGER IF EXISTS trg_actividad_ad $$
CREATE TRIGGER trg_actividad_ad AFTER DELETE ON Actividad FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Actividad', 'DELETE', OLD.ID_Actividad, CURRENT_USER(),
            CONCAT('Eliminada actividad del ', OLD.Dia, ' ', OLD.Hora_Inicio, '-', OLD.Hora_Fin));
END $$

-- DOCENTE
DROP TRIGGER IF EXISTS trg_docente_ai $$
CREATE TRIGGER trg_docente_ai AFTER INSERT ON Docente FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Docente', 'INSERT', NEW.DNI, CURRENT_USER(), CONCAT('Nombre=', NEW.Nombre));
END $$

DROP TRIGGER IF EXISTS trg_docente_au $$
CREATE TRIGGER trg_docente_au AFTER UPDATE ON Docente FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Docente', 'UPDATE', NEW.DNI, CURRENT_USER(), CONCAT('Modalidad=', NEW.Modalidad));
END $$

DROP TRIGGER IF EXISTS trg_docente_ad $$
CREATE TRIGGER trg_docente_ad AFTER DELETE ON Docente FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Docente', 'DELETE', OLD.DNI, CURRENT_USER(), CONCAT('Eliminado: ', OLD.Nombre));
END $$

-- DOCENTE_ACTIVIDAD
DROP TRIGGER IF EXISTS trg_docente_actividad_ai $$
CREATE TRIGGER trg_docente_actividad_ai AFTER INSERT ON Docente_Actividad FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Docente_Actividad', 'INSERT', CONCAT(NEW.DNI_Docente, '-', NEW.ID_Actividad), CURRENT_USER(),
            CONCAT('Rol=', NEW.Rol_Asumido));
END $$

DROP TRIGGER IF EXISTS trg_docente_actividad_ad $$
CREATE TRIGGER trg_docente_actividad_ad AFTER DELETE ON Docente_Actividad FOR EACH ROW
BEGIN
    INSERT INTO Bitacora (Tabla_Afectada, Operacion, Registro_Afectado, Usuario, Detalle)
    VALUES ('Docente_Actividad', 'DELETE', CONCAT(OLD.DNI_Docente, '-', OLD.ID_Actividad), CURRENT_USER(),
            'Asignación docente-actividad eliminada');
END $$

DELIMITER ;
