from flask import Flask, request, render_template_string, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Aquí usamos tu variable segura configurada en Render
app.secret_key = os.environ.get('SECRET_KEY', 'clave_desarrollo_local')

# Configuración de la Base de Datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    role = db.Column(db.String(20))

# Crear la base de datos e insertar usuarios de prueba al iniciar
with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username='admin', password='123', role='Administrador'))
        db.session.add(User(username='alumno', password='123', role='Estudiante'))
        db.session.commit()

# --- VISTAS HTML (FRONTEND) ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Portal Institucional - TEC AZUAY</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a237e; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); text-align: center; width: 320px; }
        h2 { color: #1a237e; margin-bottom: 5px; }
        h4 { color: #7f8c8d; margin-top: 0; font-weight: normal; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        .btn-primary { width: 100%; padding: 12px; background-color: #283593; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 10px;}
        .btn-guest { width: 100%; padding: 12px; background-color: white; color: #283593; border: 1px solid #283593; border-radius: 8px; cursor: pointer; font-size: 14px; margin-top: 20px;}
        .error { color: #e74c3c; font-size: 14px; margin-bottom: 10px;}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>TEC AZUAY</h2>
        <h4>INSTITUTO UNIVERSITARIO</h4>
        <hr style="border: 1px solid #283593; margin-bottom: 20px;">
        <p style="color: #283593; font-weight: bold;">Iniciar sesión (ingresar)</p>
        
        <p class="error">{{ error }}</p>
        
        <form method="POST">
            <input type="text" name="username" placeholder="👤 Usuario" required>
            <input type="password" name="password" placeholder="🔒 Contraseña" required>
            <button type="submit" class="btn-primary">Iniciar sesión</button>
        </form>
        
        <form method="POST" action="/guest">
            <button type="submit" class="btn-guest">Ingresar como invitado</button>
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
    <title>Dashboard - Campus Virtual</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; padding: 30px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #1a237e; }
        .role-badge { background-color: #283593; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; }
        .content { margin-top: 30px; padding: 20px; background-color: #e8eaf6; border-radius: 8px; border-left: 5px solid #3f51b5; }
        .btn-logout { display: inline-block; margin-top: 30px; padding: 10px 20px; background-color: #e53935; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bienvenido, {{ user.username }}</h1>
        <p>Tu nivel de acceso actual es: <span class="role-badge">{{ user.role }}</span></p>
        
        <div class="content">
            {% if user.role == 'Administrador' %}
                <h3>Panel de Administración (Modo PaaS)</h3>
                <p>✔️ Tienes acceso a la gestión de la base de datos completa.</p>
                <p>✔️ Puedes modificar configuraciones de seguridad del entorno.</p>
            {% elif user.role == 'Estudiante' %}
                <h3>Panel de Estudiante</h3>
                <p>✔️ Tienes acceso a tus calificaciones y cursos activos.</p>
                <p>❌ No tienes permisos de configuración del sistema.</p>
            {% else %}
                <h3>Panel de Invitado</h3>
                <p>✔️ Acceso de solo lectura a información pública.</p>
                <p>❌ Acceso denegado a registros académicos y bases de datos.</p>
            {% endif %}
        </div>
        
        <a href="/logout" class="btn-logout">Cerrar Sesión</a>
    </div>
</body>
</html>
"""

# --- RUTAS Y LÓGICA (BACKEND) ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        # Consultar a la base de datos
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            error = 'Credenciales incorrectas'
    return render_template_string(HTML_LOGIN, error=error)

@app.route('/guest', methods=['POST'])
def guest():
    session['user_id'] = 'guest'
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    if session['user_id'] == 'guest':
        user = {'username': 'Invitado Anónimo', 'role': 'Invitado'}
    else:
        user = User.query.get(session['user_id'])
        
    return render_template_string(HTML_DASHBOARD, user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)