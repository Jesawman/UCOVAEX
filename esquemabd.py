import sqlite3


def obtener_esquema_base_datos(nombre_bd):
    conexion = sqlite3.connect(nombre_bd)
    cursor = conexion.cursor()

    # Obtener la lista de tablas en la base de datos
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()

    esquema = ""

    # Obtener el esquema de cada tabla
    for tabla in tablas:
        nombre_tabla = tabla[0]
        esquema += f"Tabla: {nombre_tabla}\n"

        # Obtener las columnas de la tabla
        cursor.execute(f"PRAGMA table_info({nombre_tabla});")
        columnas = cursor.fetchall()

        for columna in columnas:
            nombre_columna = columna[1]
            tipo_dato = columna[2]
            esquema += f"\tColumna: {nombre_columna}, Tipo de dato: {tipo_dato}\n"

        esquema += "\n"

    # Cerrar la conexión con la base de datos
    conexion.close()

    return esquema

# Llamar a la función para obtener el esquema de la base de datos
nombre_bd = "database.db"
esquema_bd = obtener_esquema_base_datos(nombre_bd)

# Imprimir el esquema de la base de datos
print(esquema_bd)
