import datetime
import sqlite3
import threading
import uuid

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from jinja2 import Environment, FileSystemLoader
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey'
logged_in = False

login_manager = LoginManager()
login_manager.init_app(app)

class User:
    def __init__(self, username, tipo):
        self.username = username
        self.tipo = tipo

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username
    
@login_manager.user_loader
def load_user(username):
    tipo = obtener_tipo_de_usuario(username)
    return User(username, tipo)

def obtener_tipo_de_usuario(username):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT tipo FROM usuarios WHERE nombre_usuario = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    conn.close()

    if result is not None:
        return result[0]
    else:
        return "alumno"


@app.route('/')
def index():
    return redirect(url_for('login'))

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.teardown_appcontext
def close_db(error):
    if hasattr(threading.current_thread(), 'sqlite_db'):
        threading.current_thread().sqlite_db.close()

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=60)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    tipo = "alumno"
    if request.method == 'POST':
        with get_db() as conn:
            global logged_in
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE nombre_usuario=?", (request.form['username'],))
            login_user_dict = c.fetchone()

            if login_user_dict:
                if check_password_hash(login_user_dict[3], request.form['password']):
                    user_obj = User(login_user_dict[2], tipo)
                    login_user(user_obj)
                    logged_in = True
                    if login_user_dict[1] == 'alumno':
                        return redirect(url_for('solicitud'))
                    elif login_user_dict[1] == 'comision':
                        return redirect(url_for('administracion'))
                    elif login_user_dict[1] == 'administrador':
                        return redirect(url_for('administracion'))
                else:
                    new_hash = generate_password_hash(request.form['password'])
                    c.execute("UPDATE usuarios SET password=? WHERE nombre_usuario=?", (new_hash, request.form['username']))
                    flash('Contraseña incorrecta')
                    return redirect(url_for('login'))
            else:
                flash('Usuario no encontrado')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        tipo = request.form['tipo']
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE nombre_usuario=?", (username,))
        existing_user = c.fetchone()

        if existing_user is None:
            hashpass = generate_password_hash(password)
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (nombre_usuario, password, tipo) VALUES (?, ?, ?)", (username, hashpass, tipo))
            
            if tipo == 'comision':
                c.execute("INSERT INTO comisiones (usuario, comision) VALUES (?, ?)", (username, 'no asignada'))
                
            conn.commit()
            flash('Usuario registrado')
            conn.close()
            return redirect(url_for('administracion'))
        
        conn.close()
        flash('El nombre de usuario ya existe')
        return redirect(url_for('register'))
    
    return render_template('register.html')

asignaturas = []

@app.route('/solicitud', methods=['GET', 'POST'])
@login_required
def solicitud():
    if current_user.tipo == 'alumno':
        if request.method == 'POST':
            if 'nombre' in request.form:
                titulacion = request.form.get('titulacion')
                codigo = request.form.get('codigo')
                nombre = request.form.get('nombre')
                ects = request.form.get('ects')
                destino = request.form.get('destino')
                duracion = request.form.get('duracion')

                return render_template('solicitud.html', titulacion=titulacion, codigo=codigo, nombre=nombre, ects=ects,
                                        destino=destino, duracion=duracion, mostrar_tabla=True, asignaturas=asignaturas)
            elif 'nombre-asignatura' in request.form:
                nombre_asignatura = request.form.get('nombre-asignatura')
                codigo_asignatura = request.form.get('codigo-asignatura')
                ects_asignatura = request.form.get('ects-asignatura')
                url_asignatura = request.form.get('url-asignatura')

                asignaturas.append({
                    'nombre': nombre_asignatura,
                    'codigo': codigo_asignatura,
                    'ects': ects_asignatura,
                    'url': url_asignatura
                })

                return render_template('solicitud.html', mostrar_formulario_asignatura=True, asignaturas=asignaturas)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT nombre FROM paises")
        paises = cursor.fetchall()
        db.close()

        return render_template('solicitud.html', paises=paises)

    else:
        logout_user()
        flash('Acceso denegado. Por favor, inicia sesión con el usuario correcto.')
        return redirect(url_for('login'))

@app.route('/solicitud/<int:id>/eliminar', methods=['GET'])
@login_required
def eliminar_solicitud(id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM solicitudes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Solicitud eliminada')
    return redirect(url_for('solicitud'))

def get_nombre_asignatura_uco(codigo_asignatura_uco):
    conn = get_db();
    cursor = conn.cursor()
    cursor.execute('SELECT nombre_uco FROM asignaturas_uco WHERE codigo_asignatura_uco = ?',
                   (codigo_asignatura_uco,))
    asignatura_uco = cursor.fetchone()
    
    if asignatura_uco:
        return asignatura_uco[0]
    else:
        return None
app.jinja_env.globals.update(get_nombre_asignatura_uco=get_nombre_asignatura_uco)
    
def get_nombre_asignatura_exterior(codigo_asignatura_extranjero):
    conn = get_db();
    cursor = conn.cursor()
    cursor.execute('SELECT nombre_extranjero FROM asignaturas_exterior WHERE codigo_asignatura_extranjero = ?', 
                   (codigo_asignatura_extranjero,))
    asignatura_exterior = cursor.fetchone()
    
    if asignatura_exterior:
        return asignatura_exterior[0]
    else:
        return None
app.jinja_env.globals.update(get_nombre_asignatura_exterior=get_nombre_asignatura_exterior)

@app.route('/enviar-solicitud', methods=['POST'])
@login_required
def enviar_solicitud():
    solicitud = request.get_json()
    solicitudes = solicitud['solicitudes']

    with get_db() as conn:
        c = conn.cursor()
        id_solicitud = str(uuid.uuid4())

        usuario_comision_mapping = {
            'Grado Ingeniería Informática': 'comision_gii',
            'Grado Ingeniería Eléctrica': 'comision_gie',
            'Grado Ingeniería Mecánica': 'comision_gim',
            'Grado Ingeniería Electrónica Industrial': 'comision_giei',
            'Doble Grado Ingeniería Energía y Rec. Minerales e Ing. Eléctrica': 'comision_mii'
        }

        for solicitud in solicitudes:
            datos = solicitud['datos']
            asignaturas = solicitud['asignaturas']

            for dato in datos:
                titulacion = dato['titulacion']
                codigo = dato['codigo']
                nombre = dato['nombre']
                ects = dato['ects']
                destino = dato['destino']
                duracion = dato['duracion']

                c.execute("INSERT INTO asignatura_eps (titulacion, codigo, nombre, ects, destino, duracion) VALUES (?, ?, ?, ?, ?, ?)",
                          (titulacion, codigo, nombre, ects, destino, duracion))

                asignatura_eps_id = c.lastrowid
                c.execute("SELECT codigo, nombre FROM asignatura_eps WHERE id = ?", (asignatura_eps_id,))
                row = c.fetchone()
                codigo_eps = row[0]
                nombre_eps = row[1]

                for asignatura in asignaturas:
                    nombre_destino = asignatura['nombre']
                    codigo_destino = asignatura['codigo']
                    ects_destino = asignatura['ects']
                    url = asignatura['url']

                    c.execute("INSERT INTO asignatura_destino (codigo, nombre, ects, url) VALUES (?, ?, ?, ?)",
                              (codigo_destino, nombre_destino, ects_destino, url))

                    c.execute("INSERT INTO relacion_asignaturas (codigo_eps, nombre_eps, codigo_destino, nombre_destino) VALUES (?, ?, ?, ?)",
                              (codigo_eps, nombre_eps, codigo_destino, nombre_destino))

                    c.execute("INSERT INTO relacion_asignaturas_alumnos (id_solicitud, usuario, codigo_eps, nombre_eps, codigo_destino, nombre_destino, estado, destino) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                              (id_solicitud, current_user.get_id(), codigo_eps, nombre_eps, codigo_destino, nombre_destino, "pendiente", destino))

                usuario_comision = usuario_comision_mapping.get(titulacion, 'comision_default')
                c.execute("INSERT INTO asignaciones (id_solicitud, usuario_comision) VALUES (?, ?)",
                          (id_solicitud, usuario_comision))

        conn.commit()

    return redirect(url_for('solicitud'))

@app.route('/comentarios', methods=['GET', 'POST'])
@login_required
def comentarios():
    if request.method == 'POST':
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE solicitudes SET comentarios = ? WHERE id = ?", (request.form['comentarios'], request.form['_id']))
            conn.commit()
            flash('Comentarios guardados')
            return redirect(url_for('comentarios'))
    with get_db() as conn:
        c = conn.cursor()
        solicitudes = c.execute("SELECT * FROM solicitudes").fetchall()
    return render_template('comentarios.html', solicitudes=solicitudes)

@app.route('/administracion', methods=['GET', 'POST'])
@login_required
def administracion():
    if current_user.tipo == 'administrador' or current_user.tipo == 'asistente' or current_user.tipo == 'comision':
        if request.method == 'POST':
            with get_db() as conn:
                c = conn.cursor()
                c.execute('UPDATE solicitudes SET estado = ? WHERE id = ?',
                            (request.form['estado'], request.form['_id']))
                conn.commit()
                flash('Solicitud actualizada')
                return redirect(url_for('administracion'))
        with get_db() as conn:
            c = conn.cursor()

            c.execute('''
                SELECT usuario, destino,MAX(fecha) AS fecha, estado
                FROM relacion_asignaturas_alumnos
                GROUP BY usuario
                ORDER BY usuario ASC
            ''')
            solicitudes = c.fetchall()
            
            return render_template('administracion.html', solicitudes=solicitudes)
    else:
        logout_user()
        flash('Acceso denegado. Por favor, inicia sesión con el usuario correcto.')
        return redirect(url_for('login'))
    
def obtener_url_asignatura(codigo_asignatura):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT url
        FROM asignatura_destino
        WHERE codigo = ?
    """, (codigo_asignatura,))
    url_result = cursor.fetchone()
    url = url_result[0] if url_result else None
    
    connection.close()
    return url

def obtener_ects_asignatura(codigo_asignatura):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT ects
        FROM asignatura_eps
        WHERE codigo = ?
    """, (codigo_asignatura,))
    ects_result = cursor.fetchone()

    if ects_result:
        ects = ects_result[0]
    else:
        cursor.execute("""
            SELECT ects
            FROM asignatura_destino
            WHERE codigo = ?
        """, (codigo_asignatura,))
        ects_result = cursor.fetchone()
        ects = ects_result[0] if ects_result else None
    connection.close()
    return ects


@app.route('/usuario/<nombre_usuario>')
@login_required
def mostrar_solicitudes_usuario(nombre_usuario):
    if current_user.tipo == 'administrador' or current_user.tipo == 'asistente' or current_user.tipo == 'comision' or current_user.tipo == "alumno":

        connection = get_db()
        cursor = connection.cursor()

        cursor.execute("SELECT usuario FROM relacion_asignaturas_alumnos WHERE usuario = ?", (nombre_usuario,))
        alumno_row = cursor.fetchone()
        if alumno_row is not None:
            alumno = alumno_row[0]
        else:
            alumno = None

        comentarios = obtener_comentarios()

        cursor.execute("""
            SELECT destino
            FROM asignatura_eps
            WHERE codigo IN (
                SELECT codigo_eps
                FROM relacion_asignaturas_alumnos
                WHERE usuario = ?
            )
            LIMIT 1
        """, (nombre_usuario,))
        destino_result = cursor.fetchone()
        if destino_result is not None:
            destino = destino_result[0]
        else:
            destino = None

        cursor.execute("""
            SELECT fecha
            FROM relacion_asignaturas_alumnos
            WHERE usuario = ?
            ORDER BY id_solicitud, nombre_eps
        """, (nombre_usuario,))
        fecha = cursor.fetchall()

        fechas = []
        for f in fecha:
            fecha = f[0]
            fechas.append(fecha)

        cursor.execute("""
            SELECT id_solicitud
            FROM relacion_asignaturas_alumnos
            WHERE usuario = ?
            ORDER BY id_solicitud, nombre_eps
        """, (nombre_usuario,))
        id_solicitud_aux = cursor.fetchall()

        vector_id_solicitud = []
        for id in id_solicitud_aux:
            id_solicitud_aux = id[0]
            vector_id_solicitud.append(id_solicitud_aux)

        cursor.execute("""
            SELECT id_solicitud, nombre_eps, codigo_eps, nombre_destino, codigo_destino, estado, fecha
            FROM relacion_asignaturas_alumnos
            WHERE usuario = ?
            ORDER BY id_solicitud, nombre_eps
        """, (nombre_usuario,))
        solicitudes = cursor.fetchall()

        cursor.execute("""
            SELECT tipo
            FROM usuarios
            WHERE nombre_usuario = ?
        """, (current_user.get_id(),))
        tipo_usuario_row = cursor.fetchone()
        if tipo_usuario_row is not None:
            tipo_usuario = tipo_usuario_row[0]
        else:
            tipo_usuario = None
        print("tipo_usuario:")
        print(tipo_usuario)

        connection.close()

        grupos_solicitudes = {}
        for solicitud in solicitudes:
            id_solicitud = solicitud[0]
            nombre_eps = solicitud[1]
            codigo_eps = solicitud[2]
            nombre_destino = solicitud[3]
            codigo_destino = solicitud[4]
            estado = solicitud[5]
            fecha = solicitud[6]

            asignatura_uco = nombre_eps if nombre_eps else codigo_eps

            if asignatura_uco in grupos_solicitudes:
                grupos_solicitudes[asignatura_uco].append({
                    'nombre_uco': nombre_eps,
                    'codigo_uco': codigo_eps,
                    'nombre_destino': nombre_destino,
                    'codigo_destino': codigo_destino,
                    'ects_uco': obtener_ects_asignatura(codigo_eps),
                    'ects_destino': obtener_ects_asignatura(codigo_destino),
                    'url': obtener_url_asignatura(codigo_destino),
                    'estado': estado,
                    'fecha' : fecha

                })
            else:
                grupos_solicitudes[asignatura_uco] = [{
                    'nombre_uco': nombre_eps,
                    'codigo_uco': codigo_eps,
                    'nombre_destino': nombre_destino,
                    'codigo_destino': codigo_destino,
                    'ects_uco': obtener_ects_asignatura(codigo_eps),
                    'ects_destino': obtener_ects_asignatura(codigo_destino),
                    'url': obtener_url_asignatura(codigo_destino),
                    'estado': estado,
                    'fecha' : fecha
                }]

        if alumno is None and current_user.tipo == 'alumno':
            return render_template('solicitud.html')
        elif alumno is None:
            return render_template('administracion.html')

        return render_template('alumno_sol.html', alumno=alumno, destino=destino, grupos_solicitudes=grupos_solicitudes, usuario_tipo=tipo_usuario, comentarios=comentarios, vector_id_solicitud=vector_id_solicitud, fechas=fechas)
    else:
        logout_user()
        flash('Acceso denegado. Por favor, inicia sesión como alumno.')
        return redirect(url_for('login'))
    
@app.route('/aprobar', methods=['POST'])
@login_required
def aprobar_solicitud():
    codigo_uco = request.form['codigo_uco']

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("UPDATE relacion_asignaturas_alumnos SET estado = 'aprobado' WHERE codigo_eps = ?", (codigo_uco,))
    connection.commit()

    connection.close()

    flash('Solicitud aprobada con éxito', 'success')
    return redirect(request.referrer)


@app.route('/denegar', methods=['POST'])
@login_required
def denegar_solicitud():
    codigo_uco = request.form['codigo_uco']

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("UPDATE relacion_asignaturas_alumnos SET estado = 'denegado' WHERE codigo_eps = ?", (codigo_uco,))
    connection.commit()

    connection.close()

    flash('Solicitud denegada', 'danger')
    return redirect(request.referrer)


@app.route('/enviar', methods=['POST'])
@login_required
def enviar_comision():
    codigo_uco = request.form['codigo_uco']

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("UPDATE relacion_asignaturas_alumnos SET estado = 'enviada' WHERE codigo_eps = ?", (codigo_uco,))
    connection.commit()

    connection.close()

    flash('Solicitud enviada', 'info')
    return redirect(request.referrer)

@app.route("/guardar_comentario", methods=["POST"])
@login_required
def guardar_comentario():
    alumno = request.form.get("alumno")
    asignatura = request.form.get("asignatura")
    comentario = request.form.get("comentario")

    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO comentarios (alumno, asignatura, comentario) VALUES (?, ?, ?)",
                   (alumno, asignatura, comentario))
    connection.commit()
    connection.close()

    return "Comentario guardado correctamente"

def obtener_comentarios():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT alumno, asignatura, comentario FROM comentarios")
    comentarios = cursor.fetchall()
    connection.close()

    return comentarios

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    result = cur.fetchall()
    conn.commit()
    conn.close()
    return (result[0] if result else None) if one else result

@app.route('/comisiones', methods=['GET', 'POST'])
@login_required
def comisiones():
    if current_user.tipo == 'administrador':
        if request.method == 'POST':
            conn = get_db()
            cursor = conn.cursor()

            comision = request.form.get('comision')
            usuario = request.form.get('usuario')

            cursor.execute("INSERT OR REPLACE INTO comisiones (usuario, comision) VALUES (?, ?);", (usuario, comision))
            conn.commit()
            conn.close()

            flash('Comisión actualizada exitosamente.')

        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT usuario, comision FROM comisiones ORDER BY comision")
        comisiones = cursor.fetchall()

        return render_template('comisiones.html', user=current_user, comisiones=comisiones)
    else:
        logout_user()
        flash('Acceso denegado. Inicia sesión como usuario de comisión.')
        return redirect(url_for('login'))

@app.route('/database', methods=['GET', 'POST'])
@login_required
def database():
    if current_user.tipo == 'administrador':
        tables = query_db("SELECT name FROM sqlite_master WHERE type='table';")
        selected_table = request.form.get('table_name')
        
        if selected_table:
            columns = query_db(f"PRAGMA table_info({selected_table});")
            rows = query_db(f"SELECT * FROM {selected_table};")
            return render_template('database.html', tables=tables, selected_table=selected_table, columns=columns, rows=rows)
        
        return render_template('database.html', tables=tables, selected_table=None)
    else:
        logout_user()
        flash('Acceso denegado. Por favor, inicia sesión como alumno.')
        return redirect(url_for('login'))

@app.route('/edit/<table_name>/<int:row_id>', methods=['POST'])
@login_required
def edit_row(table_name, row_id):
    columns = query_db(f"PRAGMA table_info({table_name});")

    update_values = []
    for column in columns[1:]:
        value = request.form.get(f'col_{column[1]}')
        update_values.append(value)

    update_values.append(row_id)

    update_query = f"UPDATE {table_name} SET {', '.join([f'{column[1]}=?' for column in columns[1:]])} WHERE rowid = ?"

    query_db(update_query, update_values)

    return redirect(url_for('database'))

@app.route('/add/<table_name>', methods=['POST'])
@login_required
def add_row(table_name):
    columns = query_db(f"PRAGMA table_info({table_name});")
    
    new_values = [request.form.get(f'add_{column[1]}') for column in columns]
    placeholders = ', '.join(['?' for _ in columns])
    
    insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
    
    query_db(insert_query, new_values)
    
    return redirect(url_for('database'))

@app.route('/delete/<table_name>/<int:row_id>', methods=['POST'])
@login_required
def delete_row(table_name, row_id):
    delete_query = f"DELETE FROM {table_name} WHERE rowid = ?"
    
    query_db(delete_query, [row_id])
    
    return 'Fila eliminada', 200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    global logged_in
    logged_in = False
    flash('Has cerrado sesión.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
