import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash,session
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import threading

app = Flask(__name__)
app.secret_key = 'secretkey'

login_manager = LoginManager()
login_manager.init_app(app)

class User:
    def __init__(self, username):
        self.username = username

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
    return User(username)

@app.route('/')
def index():
    return render_template('index.html')

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.teardown_appcontext
def close_db(error):
    if hasattr(threading.current_thread(), 'sqlite_db'):
        threading.current_thread().sqlite_db.close()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE nombre_usuario=?", (request.form['username'],))
            login_user_dict = c.fetchone()

            if login_user_dict:
                if check_password_hash(login_user_dict[3], request.form['password']):
                    user_obj = User(login_user_dict[2])
                    login_user(user_obj)
                    if login_user_dict[1] == 'alumno':
                        return redirect(url_for('solicitud'))
                    elif login_user_dict[1] == 'comision':
                        return redirect(url_for('comentarios'))
                    elif login_user_dict[1] == 'administrador':
                        return redirect(url_for('administracion'))
                else:
                    new_hash = generate_password_hash(request.form['password'])
                    c.execute("UPDATE usuarios SET contrasenia=? WHERE nombre_usuario=?", (new_hash, request.form['username']))
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
            conn.commit()
            flash('Usuario registrado')
            conn.close()
            return redirect(url_for('login'))
        
        conn.close()
        flash('El nombre de usuario ya existe')
        return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/solicitud', methods=['GET', 'POST'])
@login_required
def solicitud():
    if request.method == 'POST':
        with get_db() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO solicitudes(apellidos_y_nombre_alumno, codigo_asignatura_uco, codigo_asignatura_extranjero, codigo_solicitud, fecha_solicitud, estado, comentarios) VALUES (?, ?, ?, ?, ?, ?, ?)", (request.form['nombre'], request.form['asignatura_uco'], request.form['asignatura_extranjero'], c.execute('SELECT COUNT(*) FROM solicitudes').fetchone()[0] + 1, datetime.datetime.now(), "Por aprobar", ""))
            conn.commit()
            flash('Solicitud enviada')
            return redirect(url_for('solicitud'))
    
    with get_db() as conn:
        c = conn.cursor()
        # Obtener todas las solicitudes del usuario actual
        solicitudes = c.execute("SELECT * FROM solicitudes WHERE apellidos_y_nombre_alumno = ?", (current_user.get_id(),)).fetchall()
        # Obtener todas las asignaturas UCO
        asignaturas_uco = c.execute("SELECT * FROM asignaturas_uco").fetchall()
        # Obtener todas las asignaturas en el extranjero
        asignaturas_exterior = c.execute("SELECT * FROM asignaturas_exterior").fetchall()
    
    # Renderizar la plantilla solicitud.html y pasar las solicitudes y asignaturas a ella
    return render_template('solicitud.html', solicitudes=solicitudes, asignaturas_uco=asignaturas_uco, asignaturas_exterior=asignaturas_exterior)

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

@app.route('/comentarios', methods=['GET', 'POST'])
@login_required
def comentarios():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE solicitudes SET comentarios = ? WHERE id = ?', (request.form['comentarios'], request.form['_id']))
        c.commit()
        flash('Comentarios guardados')
        return redirect(url_for('comentarios'))
    conn = sqlite3.connect('database.db')
    cur = c.execute('SELECT * FROM solicitudes')
    solicitudes = cur.fetchall()
    return render_template('comentarios.html', solicitudes=solicitudes)

@app.route('/administracion', methods=['GET', 'POST'])
@login_required
def administracion():
    conn=get_db();
    if request.method == 'POST':
        # Actualización de la solicitud en la base de datos
        cursor = conn.cursor()
        cursor.execute('UPDATE solicitudes SET estado = ? WHERE _id = ?', 
                       (request.form['estado'], request.form['_id']))
        conn.commit()
        flash('Solicitud actualizada')
        return redirect(url_for('administracion'))
    
    # Obtener solicitudes de la base de datos
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM solicitudes')
    solicitudes = cursor.fetchall()
    
    return render_template('administracion.html', solicitudes=solicitudes)


@app.route('/agregar_asignatura', methods=['GET', 'POST'])
@login_required
def agregar_asignatura():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        if 'asignatura_uco' in request.form:
            c.execute('INSERT INTO asignaturas_uco (codigo_asignatura_uco, nombre_uco, ects_uco) VALUES (?, ?, ?)',
            (request.form['codigo_asignatura_uco'], request.form['nombre_uco'], request.form['ects_uco']))
        elif 'asignatura_exterior' in request.form:
            c.execute('INSERT INTO asignaturas_exterior (codigo_asignatura_extranjero, nombre_extranjero, url, ects_extranjero) VALUES (?, ?, ?, ?)',
            (request.form['codigo_asignatura_extranjero'], request.form['nombre_extranjero'], request.form['url'], request.form['ects_extranjero']))
            conn.commit()
            flash('Asignatura añadida correctamente')
            return redirect(url_for('agregar_asignatura'))
    return render_template('agregar_asignatura.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.')
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
