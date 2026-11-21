-- =========================================================================
-- USUARIO DE APLICACIÓN
-- Crea un usuario de MySQL dedicado para que el aplicativo Python se
-- conecte (en vez de usar la cuenta root). Ejecuta este script UNA SOLA
-- VEZ, conectada como root (o el usuario administrador que uses en
-- MySQL Workbench), antes de iniciar la aplicación.
--
-- Si prefieres otro usuario/contraseña, cámbialos aquí y en las variables
-- de entorno DB_USER y DB_PASSWORD de la aplicación (ver README).
-- =========================================================================

CREATE USER IF NOT EXISTS 'app_horarios'@'localhost' IDENTIFIED BY 'horarios2026';
GRANT ALL PRIVILEGES ON bd_horarios_esclavas.* TO 'app_horarios'@'localhost';
FLUSH PRIVILEGES;
