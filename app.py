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

# --- MODELO DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200)) # Ahora guardamos un Hash seguro
    role = db.Column(db.String(20))

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer)
    materia = db.Column(db.String(100))
    estado = db.Column(db.String(50))

# Inicialización segura
with app.app_context():
    db.create_all()
    # Si la base está vacía, creamos los usuarios iniciales con contraseñas CIFRADAS
    if not User.query.first():
        hash_admin = generate_password_hash('AdminSeguro2026!')
        hash_alumno = generate_password_hash('Estudiante#1')
        hash_docente = generate_password_hash('ProfeCyber24')
        
        db.session.add(User(username='admin', password_hash=hash_admin, role='Administrador'))
        db.session.add(User(username='alumno', password_hash=hash_alumno, role='Estudiante'))
        db.session.add(User(username='profesor', password_hash=hash_docente, role='Docente'))
        db.session.commit()

# --- VISTAS HTML (Simplificadas para un solo archivo) ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Portal - TEC AZUAY</title>
    <style>
        body { font-family: sans-serif; background: #1a237e; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: white; padding: 40px; border-radius: 10px; width: 300px; text-align: center; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #283593; color: white; border: none; cursor: pointer; margin-top:10px; }
        .msg { color: red; font-size: 14px; }
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
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #1a237e; color: white; }
        .btn { padding: 8px 15px; background: #e53935; color: white; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 20px;}
        .btn-green { background: #43a047; color: white; border: none; padding: 10px; cursor: pointer; }
        input, select { padding: 8px; margin-right: 10px; }
        .alert { background: #d4edda; color: #155724; padding: 10px; margin-bottom: 15px; border-radius: 4px;}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bienvenido, {{ user.username }} ({{ user.role }})</h1>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}<div class="alert">{{ messages[0] }}</div>{% endif %}
        {% endwith %}

        <!-- PANEL DE ADMINISTRADOR -->
        {% if user.role == 'Administrador' %}
            <h3>Gestión de Usuarios (Base de Datos PaaS)</h3>
            <form action="/add_user" method="POST" style="background:#e8eaf6; padding:15px; border-radius:5px;">
                <input type="text" name="new_username" placeholder="Nuevo Usuario" required>
                <input type="password" name="new_password" placeholder="Contraseña (se cifrará)" required>
                <select name="new_role">
                    <option value="Estudiante">Estudiante</option>
                    <option value="Docente">Docente</option>
                </select>
                <button type="submit" class="btn-green">Crear Usuario</button>
            </form>
            
            <table>
                <tr><th>ID</th><th>Usuario</th><th>Rol</th><th>Hash de Contraseña (Seguro)</th></tr>
                {% for u in all_users %}
                <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.role }}</td><td style="font-size:10px;">{{ u.password_hash[:20] }}...</td></tr>
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
                            <button type="submit" class="btn-green">Simular Entrega de Tarea</button>
                        </form>
                    </td>
                </tr>
                <tr><td>Arquitecturas Cloud (PaaS)</td><td>Prof. Admin</td>
                    <td>
                        <form action="/submit_task" method="POST">
                            <input type="hidden" name="materia" value="Cloud">
                            <button type="submit" class="btn-green">Simular Entrega de Tarea</button>
                        </form>
                    </td>
                </tr>
            </table>
            
            <h3>Historial de Entregas</h3>
            <ul>
                {% for t in tareas %}
                <li>Has entregado un trabajo para: <strong>{{ t.materia }}</strong> (Estado: {{ t.estado }})</li>
                {% else %}
                <li>No tienes entregas recientes.</li>
                {% endfor %}
            </ul>
        {% endif %}
        
        <br><a href="/logout" class="btn">Cerrar Sesión</a>
    </div>
</body>
</html>
"""

# --- RUTAS ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        # Verificar que el usuario exista y que el HASH coincida con la contraseña ingresada
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect('/dashboard')
        flash('Credenciales incorrectas o usuario no existe.')
    return render_template_string(HTML_LOGIN)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    
    all_users = User.query.all() if user.role == 'Administrador' else []
    tareas = Tarea.query.filter_by(estudiante_id=user.id).all() if user.role == 'Estudiante' else []
    
    return render_template_string(HTML_DASHBOARD, user=user, all_users=all_users, tareas=tareas)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' in session:
        admin = User.query.get(session['user_id'])
        if admin.role == 'Administrador':
            nuevo_user = request.form['new_username']
            # Ciframos la contraseña antes de guardarla
            pass_hash = generate_password_hash(request.form['new_password'])
            rol = request.form['new_role']
            
            db.session.add(User(username=nuevo_user, password_hash=pass_hash, role=rol))
            db.session.commit()
            flash(f'Usuario {nuevo_user} creado con éxito.')
    return redirect('/dashboard')

@app.route('/submit_task', methods=['POST'])
def submit_task():
    if 'user_id' in session:
        materia = request.form['materia']
        db.session.add(Tarea(estudiante_id=session['user_id'], materia=materia, estado='Entregado para calificar'))
        db.session.commit()
        flash(f'Tarea de {materia} registrada exitosamente en la base de datos.')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)