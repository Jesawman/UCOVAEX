import sqlite3


def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS asignatura_eps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulacion TEXT,
                    codigo TEXT,
                    nombre TEXT,
                    ects INTEGER,
                    destino TEXT,
                    duracion TEXT
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT,
                    nombre_usuario TEXT,
                    password TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS asignatura_destino (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    codigo TEXT,
                    ects INTEGER,
                    url TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS relacion_asignaturas (
                    codigo_eps TEXT,
                    nombre_eps TEXT,
                    codigo_destino TEXT,
                    nombre_destino TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    FOREIGN KEY(codigo_eps, nombre_eps) REFERENCES asignatura_eps(codigo, nombre),
                    FOREIGN KEY(codigo_destino, nombre_destino) REFERENCES asignatura_destino(codigo, nombre),
                    PRIMARY KEY (codigo_eps, codigo_destino)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS relacion_asignaturas_alumnos (
                    usuario TEXT,
                    fecha TEXT DEFAULT (strftime('%d/%m/%Y', 'now', 'localtime')),
                    codigo_eps TEXT,
                    nombre_eps TEXT,
                    codigo_destino TEXT,
                    nombre_destino TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    FOREIGN KEY(codigo_eps, nombre_eps) REFERENCES asignatura_eps(codigo, nombre),
                    FOREIGN KEY(codigo_destino, nombre_destino) REFERENCES asignatura_destino(codigo, nombre),
                    PRIMARY KEY (codigo_eps, codigo_destino)
                )''')

    conn.commit()
    conn.close()

create_tables()
