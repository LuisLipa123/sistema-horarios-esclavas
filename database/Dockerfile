# Imagen de MySQL con la base bd_horarios_esclavas lista para usar.
# Se copian (no se montan) la configuración y los scripts para que tengan
# permisos 644: MySQL ignora archivos .cnf con permisos de escritura global,
# que es lo que ocurre al montar carpetas desde Windows.
FROM mysql:8.4

COPY conf/charset.cnf /etc/mysql/conf.d/charset.cnf
COPY init/ /docker-entrypoint-initdb.d/

RUN chmod 644 /etc/mysql/conf.d/charset.cnf /docker-entrypoint-initdb.d/*.sql
