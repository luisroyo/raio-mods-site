# DEPRECATED: Este arquivo é apenas uma fachada para evitar quebra de imports antigos.
# Por favor, importe diretamente de database.db_wrappers em novos códigos.

from database.db_wrappers import get_db_connection, PostgreSQLConnectionWrapper, PostgreSQLRow, PostgreSQLCursorWrapper
