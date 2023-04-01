from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'app'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/app'
app.config['SECRET_KEY'] = 'secretkey'

mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    u = mongo.db.usuarios.find_one({"nombre_usuario": user_id})
    if not u:
        return None
    return User(u['nombre_usuario'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = mongo.db.usuarios
        login_user_dict = usuario.find_one({'nombre_usuario' : request.form['username']})

        if login_user_dict:
            if check_password_hash(login_user_dict['password'], request.form['password']):
                user_obj = User(login_user_dict['nombre_usuario'])
                login_user(user_obj)
                if login_user_dict['tipo'] == 'alumno':
                    return redirect(url_for('solicitud'))
                elif login_user_dict['tipo'] == 'comision':
                    return redirect(url_for('comentarios'))
                elif login_user_dict['tipo'] == 'administrador':
                    return redirect(url_for('administracion'))
            else:
                flash('Contraseña incorrecta')
                return redirect(url_for('login'))
        else:
            flash('Usuario no encontrado')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuarios = mongo.db.usuarios
        existing_user = usuarios.find_one({'nombre_usuario' : request.form['username']})

        if existing_user is None:
            hashpass = generate_password_hash(request.form['password'])
            usuarios.insert_one({'nombre_usuario' : request.form['username'], 'password' : hashpass, 'tipo' : request.form['tipo']})
            flash('Usuario registrado')
            return redirect(url_for('login'))
        flash('El nombre de usuario ya existe')
        return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/solicitud', methods=['GET', 'POST'])
@login_required
def solicitud():
    if request.method == 'POST':
        solicitudes = mongo.db.solicitudes
        solicitudes.insert_one({'apellidos_y_nombre_alumno' : request.form['nombre'], 'codigo_asignatura_uco' : request.form['asignatura_uco'], 'codigo_asignatura_extranjero' : request.form['asignatura_extranjero'], 'codigo_solicitud' : solicitudes.count_documents({}) + 1, 'fecha_solicitud' : datetime.datetime.now()})
        flash('Solicitud enviada')
        return redirect(url_for('solicitud'))
    return render_template('solicitud.html', solicitudes=mongo.db.solicitudes.find({'apellidos_y_nombre_alumno' : current_user.id}), asignaturas_uco=mongo.db.asignaturas_uco.find(), asignaturas_exterior=mongo.db.asignaturas_exterior.find())

@app.route('/solicitud/<id>/eliminar', methods=['GET'])
@login_required
def eliminar_solicitud(id):
    solicitudes = mongo.db.solicitudes
    result = solicitudes.delete_one({'_id': ObjectId(id)})
    if result.deleted_count == 1:
        flash('Solicitud eliminada')
    else:
        flash('No se pudo eliminar la solicitud')
    return redirect(url_for('solicitud'))

def get_nombre_asignatura_uco(codigo_asignatura_uco):
    asignaturas_uco = mongo.db.asignaturas_uco
    asignatura_uco = asignaturas_uco.find_one({'codigo_asignatura_uco': codigo_asignatura_uco})
    if asignatura_uco:
        return asignatura_uco['nombre_uco']
    else:
        return None
app.jinja_env.globals.update(get_nombre_asignatura_uco=get_nombre_asignatura_uco)
    
def get_nombre_asignatura_exterior(codigo_asignatura_extranjero):
    asignaturas_uco = mongo.db.asignaturas_exterior
    asignatura_uco = asignaturas_uco.find_one({'codigo_asignatura_extranjero': codigo_asignatura_extranjero})
    if asignatura_uco:
        return asignatura_uco['nombre_extranjero']
    else:
        return None
app.jinja_env.globals.update(get_nombre_asignatura_exterior=get_nombre_asignatura_exterior)


@app.route('/comentarios', methods=['GET', 'POST'])
@login_required
def comentarios():
    if request.method == 'POST':
        solicitudes = mongo.db.solicitudes
        solicitudes.update_one({'_id' : ObjectId(request.form['_id'])}, {'$set' : {'comentarios' : request.form['comentarios']}})
        flash('Comentarios guardados')
        return redirect(url_for('comentarios'))
    return render_template('comentarios.html', solicitudes=mongo.db.solicitudes.find())

@app.route('/administracion', methods=['GET', 'POST'])
@login_required
def administracion():
    if request.method == 'POST':
        solicitudes = mongo.db.solicitudes
        solicitudes.update_one({'_id' : ObjectId(request.form['_id'])}, {'$set' : {'estado' : request.form['estado']}})
        flash('Solicitud actualizada')
        return redirect(url_for('administracion'))
    return render_template('administracion.html', solicitudes=mongo.db.solicitudes.find())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

