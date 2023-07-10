import sqlite3


def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def insert_data():
    conn = get_db()
    c = conn.cursor()

    c.execute("INSERT INTO asignatura_eps (titulacion, codigo, nombre, ects, destino, duracion) VALUES (?, ?, ?, ?, ?, ?)",
              ("Titulación 1", "COD001", "Asignatura 1", 6, "Destino 1", "4 años"))
    c.execute("INSERT INTO asignatura_eps (titulacion, codigo, nombre, ects, destino, duracion) VALUES (?, ?, ?, ?, ?, ?)",
              ("Titulación 2", "COD002", "Asignatura 2", 5, "Destino 2", "3 años"))

    c.execute("INSERT INTO asignatura_destino (nombre, codigo, ects, url) VALUES (?, ?, ?, ?)",
              ("Asignatura Destino 1", "COD001", 5, "https://ejemplo1.com"))
    c.execute("INSERT INTO asignatura_destino (nombre, codigo, ects, url) VALUES (?, ?, ?, ?)",
              ("Asignatura Destino 2", "COD002", 6, "https://ejemplo2.com"))

    c.execute("INSERT INTO relacion_asignaturas (codigo_eps, nombre_eps, codigo_destino, nombre_destino) VALUES (?, ?, ?, ?)",
              ("COD001", "Asignatura 1", "COD001", "Asignatura Destino 1"))
    c.execute("INSERT INTO relacion_asignaturas (codigo_eps, nombre_eps, codigo_destino, nombre_destino) VALUES (?, ?, ?, ?)",
              ("COD002", "Asignatura 2", "COD002", "Asignatura Destino 2"))

    c.execute("INSERT INTO relacion_asignaturas_alumnos (usuario, codigo_eps, nombre_eps, codigo_destino, nombre_destino) VALUES (?, ?, ?, ?, ?)",
              ("usuario1", "COD001", "Asignatura 1", "COD001", "Asignatura Destino 1"))
    c.execute("INSERT INTO relacion_asignaturas_alumnos (usuario, codigo_eps, nombre_eps, codigo_destino, nombre_destino) VALUES (?, ?, ?, ?, ?)",
              ("usuario2", "COD002", "Asignatura 2", "COD002", "Asignatura Destino 2"))

    conn.commit()
    conn.close()

insert_data()
