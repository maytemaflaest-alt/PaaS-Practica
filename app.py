from flask import Flask, request, render_template_string, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_desarrollo_local_super_segura')

# Configuración de Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200)) 
    role = db.Column(db.String(20))

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer)
    estudiante_nombre = db.Column(db.String(50))
    materia = db.Column(db.String(100))
    estado = db.Column(db.String(50))

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('AdminSeguro2026!'), role='Administrador'))
        db.session.add(User(username='alumno', password_hash=generate_password_hash('Estudiante#1'), role='Estudiante'))
        db.session.add(User(username='profesor', password_hash=generate_password_hash('ProfeCyber24'), role='Docente'))
        db.session.commit()

# --- VISTAS HTML ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Portal - TEC AZUAY</title>
    <style>
        body { font-family: sans-serif; background: #1a237e; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: white; padding: 40px; border-radius: 10px; width: 300px; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #283593; color: white; border: none; cursor: pointer; margin-top:10px; }
        .msg { color: #d32f2f; background: #ffcdd2; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#1a237e;">TEC AZUAY</h2>
        <p>Plataforma PaaS Segura</p>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="msg">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Usuario" required>
            <input type="password" name="password" placeholder="Contraseña" required>
            <button type="submit">Ingresar</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
        table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px;}
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #1a237e; color: white; }
        .btn { padding: 8px 15px; background: #e53935; color: white; text-decoration: none; border-radius: 4px; display: inline-block;}
        .btn-green { background: #43a047; color: white; border: none; padding: 8px; cursor: pointer; border-radius: 4px; }
        .btn-blue { background: #1e88e5; color: white; border: none; padding: 8px; cursor: pointer; border-radius: 4px; }
        input, select { padding: 8px; margin-right: 5px; }
        .alert { background: #d4edda; color: #155724; padding: 10px; margin-bottom: 15px; border-radius: 4px;}
        .alert-error { background: #f8d7da; color: #721c24; padding: 10px; margin-bottom: 15px; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="margin: 0; color:#1a237e;">Bienvenido, {{ user.username }} <span style="font-size:16px; color:#666;">({{ user.role }})</span></h1>
            <a href="/logout" class="btn">Cerrar Sesión</a>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="{% if category == 'error' %}alert-error{% else %}alert{% endif %}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- PANEL DE ADMINISTRADOR -->
        {% if user.role == 'Administrador' %}
            <h3>Gestión de Usuarios</h3>
            <form action="/add_user" method="POST" style="background:#e8eaf6; padding:15px; border-radius:5px;">
                <input type="text" name="new_username" placeholder="Nuevo Usuario" required>
                <input type="password" name="new_password" placeholder="Contraseña segura" required>
                <select name="new_role">
                    <option value="Estudiante">Estudiante</option>
                    <option value="Docente">Docente</option>
                </select>
                <button type="submit" class="btn-green">Crear Usuario</button>
            </form>
            
            <table>
                <tr><th>ID</th><th>Usuario</th><th>Rol</th><th>Hash de Contraseña</th></tr>
                {% for u in all_users %}
                <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.role }}</td><td style="font-size:10px; color:#666;">{{ u.password_hash[:25] }}...</td></tr>
                {% endfor %}
            </table>
            
        <!-- PANEL DE DOCENTE -->
        {% elif user.role == 'Docente' %}
            <h3>Bandeja de Calificaciones (Entregas de Estudiantes)</h3>
            <table>
                <tr><th>Alumno</th><th>Materia</th><th>Estado Actual</th><th>Acción</th></tr>
                {% for t in todas_tareas %}
                <tr>
                    <td>{{ t.estudiante_nombre }}</td>
                    <td>{{ t.materia }}</td>
                    <td><strong>{{ t.estado }}</strong></td>
                    <td>
                        <form action="/grade_task" method="POST" style="display:inline;">
                            <input type="hidden" name="tarea_id" value="{{ t.id }}">
                            <select name="calificacion">
                                <option value="Aprobado (10/10)">10/10 - Aprobado</option>
                                <option value="Revisar (7/10)">7/10 - Revisar</option>
                                <option value="Reprobado (4/10)">4/10 - Reprobado</option>
                            </select>
                            <button type="submit" class="btn-blue">Calificar</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="4" style="text-align:center;">No hay entregas pendientes en la base de datos.</td></tr>
                {% endfor %}
            </table>

        <!-- PANEL DE ESTUDIANTE -->
        {% elif user.role == 'Estudiante' %}
            <h3>Mis Cursos Actuales</h3>
            <table>
                <tr><th>Materia</th><th>Docente</th><th>Acción</th></tr>
                <tr><td>Ciberseguridad Avanzada</td><td>Prof. Admin</td>
                    <td>
                        <form action="/submit_task" method="POST">
                            <input type="hidden" name="materia" value="Ciberseguridad">
                            <button type="submit" class="btn-green">Subir Tarea / Proyecto</button>
                        </form>
                    </td>
                </tr>
                <tr><td>Arquitecturas Cloud (PaaS)</td><td>Prof. Admin</td>
                    <td>
                        <form action="/submit_task" method="POST">
                            <input type="hidden" name="materia" value="Cloud">
                            <button type="submit" class="btn-green">Subir Tarea / Proyecto</button>
                        </form>
                    </td>
                </tr>
            </table>
            
            <h3>Historial de Evaluaciones</h3>
            <ul>
                {% for t in tareas %}
                <li>Entrega de: <strong>{{ t.materia }}</strong> - Estado de calificación: <span style="color:#1e88e5; font-weight:bold;">{{ t.estado }}</span></li>
                {% else %}
                <li>No tienes entregas recientes registradas.</li>
                {% endfor %}
            </ul>
        {% endif %}
    </div>
</body>
</html>
"""

# --- RUTAS ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect('/dashboard')
        flash('Credenciales incorrectas o usuario no existe.', 'error')
    return render_template_string(HTML_LOGIN)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    
    all_users = User.query.all() if user.role == 'Administrador' else []
    tareas = Tarea.query.filter_by(estudiante_id=user.id).all() if user.role == 'Estudiante' else []
    todas_tareas = Tarea.query.all() if user.role == 'Docente' else []
    
    return render_template_string(HTML_DASHBOARD, user=user, all_users=all_users, tareas=tareas, todas_tareas=todas_tareas)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' in session:
        admin = User.query.get(session['user_id'])
        if admin.role == 'Administrador':
            nuevo_user = request.form['new_username']
            
            # SOLUCIÓN AL ERROR 500: Validar si el usuario ya existe
            if User.query.filter_by(username=nuevo_user).first():
                flash(f'Error: El usuario "{nuevo_user}" ya existe en la base de datos.', 'error')
                return redirect('/dashboard')
                
            pass_hash = generate_password_hash(request.form['new_password'])
            rol = request.form['new_role']
            db.session.add(User(username=nuevo_user, password_hash=pass_hash, role=rol))
            db.session.commit()
            flash(f'Usuario {nuevo_user} ({rol}) creado exitosamente.', 'success')
    return redirect('/dashboard')

@app.route('/submit_task', methods=['POST'])
def submit_task():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        materia = request.form['materia']
        db.session.add(Tarea(estudiante_id=user.id, estudiante_nombre=user.username, materia=materia, estado='Entregado (Pendiente de revisión)'))
        db.session.commit()
        flash(f'Tarea de {materia} registrada exitosamente.', 'success')
    return redirect('/dashboard')

@app.route('/grade_task', methods=['POST'])
def grade_task():
    if 'user_id' in session:
        docente = User.query.get(session['user_id'])
        if docente.role == 'Docente':
            tarea = Tarea.query.get(request.form['tarea_id'])
            if tarea:
                tarea.estado = request.form['calificacion']
                db.session.commit()
                flash('Calificación asignada y guardada en la base de datos.', 'success')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)