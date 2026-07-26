from flask import Flask, request, render_template_string, redirect, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_segura_v6')

# Configuración de Base de Datos y Carpeta de Subidas
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_v6.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200)) 
    role = db.Column(db.String(20))

class Archivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    propietario = db.Column(db.String(50))
    nombre_archivo = db.Column(db.String(200))
    fecha = db.Column(db.String(20))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='MAYTE').first():
        db.session.add(User(username='MAYTE', password_hash=generate_password_hash('Admin2026'), role='Administrador'))
    if not User.query.filter_by(username='alumno').first():
        db.session.add(User(username='alumno', password_hash=generate_password_hash('Estudiante#1'), role='Estudiante'))
    db.session.commit()

# --- VISTAS HTML (CLON TEC AZUAY) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TEC AZUAY - Campus Virtual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .top-card { background: white; border-radius: 15px; padding: 20px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .logo-text { color: #1a237e; font-weight: 900; font-size: 28px; margin: 0; letter-spacing: 1px;}
        .sub-logo { color: #7f8c8d; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; margin-top: -5px; }
        
        .btn-menu { border-radius: 10px; font-weight: bold; padding: 10px 20px; border: none; color: white; margin: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s;}
        .btn-menu:hover { transform: translateY(-3px); color: white;}
        .btn-tareas { background: linear-gradient(45deg, #ff9800, #ffb74d); }
        .btn-calendario { background: linear-gradient(45deg, #1a237e, #3949ab); }
        .btn-cursos { background: linear-gradient(45deg, #4caf50, #81c784); }
        .btn-mensajes { background: linear-gradient(45deg, #2196f3, #64b5f6); }
        .btn-notif { background: linear-gradient(45deg, #9c27b0, #ba68c8); }
        .btn-anuncios { background: linear-gradient(45deg, #e91e63, #f06292); }
        
        .welcome-banner { background-color: #0d1b2a; color: white; border-radius: 15px; padding: 20px 30px; margin-bottom: 20px; font-size: 24px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2);}
        
        .schedule-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .table-schedule { width: 100%; border-collapse: separate; border-spacing: 8px; text-align: center;}
        .table-schedule th { background-color: #1a237e; color: white; border-radius: 8px; padding: 10px; font-size: 12px;}
        .table-schedule td { padding: 12px; border-radius: 8px; font-size: 11px; font-weight: bold; color: white; vertical-align: middle; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
        .day-header { background-color: #f8f9fa !important; color: #1a237e !important; font-weight: bold; font-size: 14px !important; text-align: left; padding-left: 20px !important;}
        
        .bg-navy { background-color: #1a237e; }
        .bg-red { background-color: #ff5252; }
        .bg-blue { background-color: #448aff; }
        .bg-lightblue { background-color: #4fc3f7; }
        .bg-pink { background-color: #e040fb; }
    </style>
</head>
<body>
    {% if not user %}
    <div class="container d-flex justify-content-center align-items-center" style="height: 100vh;">
        <div class="card shadow-lg p-5 text-center" style="border-radius: 20px; width: 350px;">
            <h1 class="logo-text">TEC AZUAY</h1>
            <p class="sub-logo mb-4">Instituto Universitario</p>
            {% with messages = get_flashed_messages() %}{% if messages %}<div class="alert alert-danger">{{ messages[0] }}</div>{% endif %}{% endwith %}
            <form method="POST" action="/">
                <input type="text" name="username" class="form-control mb-3" placeholder="Usuario" required>
                <input type="password" name="password" class="form-control mb-3" placeholder="Contraseña" required>
                <button type="submit" class="btn btn-primary w-100 btn-calendario">Ingresar</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="container mt-4">
        <!-- HEADER -->
        <div class="top-card d-flex justify-content-between align-items-center">
            <div>
                <h1 class="logo-text">TEC AZUAY</h1>
                <p class="sub-logo">Instituto Universitario</p>
                <div style="width: 50px; height: 3px; background-color: #ffc107; margin-top: 5px;"></div>
            </div>
            <div class="d-flex align-items-center">
                <span class="me-3 fw-bold" style="color: #1a237e;"><i class="fa-solid fa-user-graduate"></i> {{ user.username }}</span>
                <a href="/logout" class="btn btn-danger rounded-pill px-4 fw-bold shadow-sm">Cerrar Sesión</a>
            </div>
        </div>

        <!-- BOTONES INTERACTIVOS -->
        <div class="d-flex flex-wrap mb-3">
            <button class="btn-menu btn-tareas" data-bs-toggle="modal" data-bs-target="#tareasModal"><i class="fa-solid fa-clipboard-list me-2"></i> Mis Tareas (Subir Archivos)</button>
            <button class="btn-menu btn-calendario" data-bs-toggle="modal" data-bs-target="#infoModal"><i class="fa-solid fa-calendar-days me-2"></i> Calendario</button>
            <button class="btn-menu btn-cursos" data-bs-toggle="modal" data-bs-target="#infoModal"><i class="fa-solid fa-book-open me-2"></i> Cursos</button>
            <button class="btn-menu btn-mensajes" data-bs-toggle="modal" data-bs-target="#infoModal"><i class="fa-solid fa-comments me-2"></i> Mensajes</button>
            <button class="btn-menu btn-notif" data-bs-toggle="modal" data-bs-target="#infoModal"><i class="fa-solid fa-bell me-2"></i> Notificaciones</button>
            <button class="btn-menu btn-anuncios" data-bs-toggle="modal" data-bs-target="#infoModal"><i class="fa-solid fa-bullhorn me-2"></i> Anuncios</button>
        </div>

        <!-- WELCOME BANNER -->
        <div class="welcome-banner">
            ¡Bienvenido, {{ user.username }}! 📚
        </div>
        
        <!-- ALERTAS -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible shadow-sm">
                        {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- HORARIO DE CLASES -->
        <div class="schedule-card">
            <h4 class="mb-4" style="color: #1a237e; font-weight: bold;"><i class="fa-regular fa-calendar-days me-2"></i> Horario de Clases</h4>
            <div class="table-responsive">
                <table class="table-schedule">
                    <thead>
                        <tr>
                            <th style="background: transparent;"></th>
                            <th>17:00 - 18:00</th>
                            <th>18:00 - 19:00</th>
                            <th>19:00 - 20:00</th>
                            <th>20:00 - 21:00</th>
                            <th>21:00 - 22:00</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="day-header">LUNES</td>
                            <td class="bg-navy">TSCSSS - HACKEO ETICO LABORATORIO<br><small>BORIS SQUILANDA<br>LAB3</small></td>
                            <td class="bg-navy">TSCSSS - HACKEO ETICO LABORATORIO<br><small>BORIS SQUILANDA<br>LAB3</small></td>
                            <td class="bg-red">TSCS - CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO<br>LAB3</small></td>
                            <td class="bg-red">TSCS - CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO<br>LAB3</small></td>
                            <td class="bg-blue">TSCS - CIBERSEGURIDAD EN TECNOLOGIAS<br><small>SHIRLEY TORRES<br>LAB3</small></td>
                        </tr>
                        <tr>
                            <td class="day-header">MARTES</td>
                            <td class="bg-blue">TSCS - CIBERSEGURIDAD EN TECNOLOGIAS<br><small>SHIRLEY TORRES<br>LAB6</small></td>
                            <td class="bg-navy">TSCSSS - HACKEO ETICO LABORATORIO<br><small>BORIS SQUILANDA<br>LAB3</small></td>
                            <td class="bg-blue">TSCS - CIBERSEGURIDAD EN TECNOLOGIAS<br><small>SHIRLEY TORRES<br>LAB6</small></td>
                            <td class="bg-lightblue">TSCS - CONTINUIDAD DEL NEGOCIO<br><small>SHIRLEY TORRES</small></td>
                            <td class="bg-lightblue">TSCS - CONTINUIDAD DEL NEGOCIO<br><small>SHIRLEY TORRES</small></td>
                        </tr>
                        <tr>
                            <td class="day-header">MIÉRCOLES</td>
                            <td class="bg-red">TSCS - CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO<br>LAB3</small></td>
                            <td class="bg-red">TSCS - CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO<br>LAB3</small></td>
                            <td class="bg-blue">TSCS - CIBERSEGURIDAD EN TECNOLOGIAS<br><small>SHIRLEY TORRES<br>LAB6</small></td>
                            <td class="bg-navy">TSCSSS - HACKEO ETICO LABORATORIO<br><small>BORIS SQUILANDA<br>LAB3</small></td>
                            <td class="bg-navy">TSCSSS - HACKEO ETICO LABORATORIO<br><small>BORIS SQUILANDA<br>LAB3</small></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="d-flex justify-content-between mt-4 text-muted small pb-5">
            <select class="form-select form-select-sm" style="width: 200px;"><option>Español (México) [es_mx]</option></select>
            <span>Aviso sobre cookies</span>
        </div>
    </div>

    <!-- MODAL DE SUBIDA DE TAREAS (INTERACCIÓN REAL) -->
    <div class="modal fade" id="tareasModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title fw-bold"><i class="fa-solid fa-upload"></i> Gestor de Tareas y Archivos</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4">
            
            <form action="/upload" method="POST" enctype="multipart/form-data" class="mb-4 p-3 border rounded bg-light">
                <h6>Subir nuevo documento (PDF, PNG, JPG)</h6>
                <div class="input-group">
                    <input type="file" name="archivo" class="form-control" required>
                    <button class="btn btn-primary" type="submit">Subir Archivo al PaaS</button>
                </div>
                <small class="text-muted">Nota PaaS: En servidores gratuitos, estos archivos se borran al reiniciar la instancia.</small>
            </form>
            
            <h6>Archivos almacenados actualmente:</h6>
            <table class="table table-bordered table-sm mt-2">
                <thead class="table-dark"><tr><th>Nombre del Documento</th><th>Subido por</th><th>Fecha</th><th>Acción</th></tr></thead>
                <tbody>
                    {% for a in archivos %}
                    <tr>
                        <td>{{ a.nombre_archivo }}</td>
                        <td>{{ a.propietario }}</td>
                        <td>{{ a.fecha }}</td>
                        <td><a href="/download/{{ a.nombre_archivo }}" class="btn btn-success btn-sm" target="_blank">Ver/Descargar</a></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="text-center text-muted">No hay archivos subidos en el servidor.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- MODAL GENÉRICO PARA OTRAS SECCIONES -->
    <div class="modal fade" id="infoModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Sección en Construcción</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body text-center p-5">
            <i class="fa-solid fa-person-digging fa-3x mb-3 text-warning"></i>
            <p>Has interactuado con una sección del Moodle. Esta vista dinámica demuestra el enrutamiento del Frontend.</p>
          </div>
        </div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% endif %}
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
        flash('Credenciales incorrectas.', 'error')
    return render_template_string(HTML_TEMPLATE, user=None)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    archivos = Archivo.query.order_by(Archivo.id.desc()).all()
    return render_template_string(HTML_TEMPLATE, user=user, archivos=archivos)

# RUTA PARA SUBIR ARCHIVOS (PDFs/Imágenes)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    
    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect('/dashboard')
        
    file = request.files['archivo']
    if file.filename == '':
        flash('El nombre del archivo está vacío.', 'error')
        return redirect('/dashboard')
        
    if file:
        filename = secure_filename(file.filename)
        # Guardar en el disco del servidor PaaS
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Registrar en la Base de Datos
        hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        db.session.add(Archivo(propietario=user.username, nombre_archivo=filename, fecha=hora_actual))
        db.session.commit()
        
        flash(f'Archivo "{filename}" subido correctamente al servidor.', 'success')
        
    return redirect('/dashboard')

# RUTA PARA DESCARGAR/VER ARCHIVOS
@app.route('/download/<filename>')
def download_file(filename):
    if 'user_id' not in session: return redirect('/')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)