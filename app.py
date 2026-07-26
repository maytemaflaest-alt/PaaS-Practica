from flask import Flask, request, render_template_string, redirect, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_segura_v7')

# Configuración Base de Datos y Subidas
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_v7.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# --- HARDENING DE SEGURIDAD ---
# 1. Límite de peticiones para evitar DoS de Capa 7 y Fuerza Bruta
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

# 2. Control estricto de extensiones de archivos (Prevención de ejecución remota de código - RCE)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 3. Inyección de Cabeceras de Seguridad HTTP (Mitigación para escáneres de vulnerabilidades)
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY' # Previene Clickjacking
    response.headers['X-Content-Type-Options'] = 'nosniff' # Previene MIME-sniffing
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains' # Fuerza HTTPS (HSTS)
    response.headers['X-XSS-Protection'] = '1; mode=block' # Filtro XSS básico
    return response

# --- MODELOS ---
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
    archivo_nombre = db.Column(db.String(200)) # NUEVO: Archivo vinculado a la tarea
    estado = db.Column(db.String(50))
    nota = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.String(20))

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    autor = db.Column(db.String(50))
    rol_autor = db.Column(db.String(20))
    texto = db.Column(db.Text)
    fecha = db.Column(db.String(20))

class MensajePrivado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remitente_id = db.Column(db.Integer)
    remitente_nombre = db.Column(db.String(50))
    destinatario_id = db.Column(db.Integer)
    destinatario_nombre = db.Column(db.String(50))
    texto = db.Column(db.Text)
    fecha = db.Column(db.String(20))

# --- INICIALIZACIÓN DE TODOS LOS USUARIOS ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='MAYTE').first():
        db.session.add(User(username='MAYTE', password_hash=generate_password_hash('Admin2026'), role='Administrador'))
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('AdminSeguro2026!'), role='Administrador'))
    if not User.query.filter_by(username='profesor').first():
        db.session.add(User(username='profesor', password_hash=generate_password_hash('ProfeCyber24'), role='Docente'))
    if not User.query.filter_by(username='alumno').first():
        db.session.add(User(username='alumno', password_hash=generate_password_hash('Estudiante#1'), role='Estudiante'))
    if not User.query.filter_by(username='Edisson').first():
        db.session.add(User(username='Edisson', password_hash=generate_password_hash('Estudiante2026'), role='Estudiante'))
    if not User.query.filter_by(username='Timoteo').first():
        db.session.add(User(username='Timoteo', password_hash=generate_password_hash('Estudiante2026'), role='Estudiante'))
    db.session.commit()

# --- HTML (Diseño Clon TEC AZUAY + Lógica V5) ---
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
        
        /* Botones estilo Tabs interactivos */
        .nav-pills .nav-link { border-radius: 10px; font-weight: bold; padding: 10px 20px; color: white; margin: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s;}
        .nav-pills .nav-link:hover { transform: translateY(-3px); color: white;}
        .nav-pills .nav-link.active { border: 2px solid #000; opacity: 0.9;}
        
        .btn-calendario { background: linear-gradient(45deg, #1a237e, #3949ab); }
        .btn-tareas { background: linear-gradient(45deg, #ff9800, #ffb74d); }
        .btn-mensajes { background: linear-gradient(45deg, #2196f3, #64b5f6); }
        .btn-admin { background: linear-gradient(45deg, #e91e63, #f06292); }
        
        .welcome-banner { background-color: #0d1b2a; color: white; border-radius: 15px; padding: 20px 30px; margin-bottom: 20px; font-size: 24px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2);}
        .card-custom { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        
        /* Estilos de Horario */
        .table-schedule { width: 100%; border-collapse: separate; border-spacing: 8px; text-align: center;}
        .table-schedule th { background-color: #1a237e; color: white; border-radius: 8px; padding: 10px; font-size: 12px;}
        .table-schedule td { padding: 12px; border-radius: 8px; font-size: 11px; font-weight: bold; color: white; vertical-align: middle;}
        .day-header { background-color: #f8f9fa !important; color: #1a237e !important; font-weight: bold; font-size: 14px !important; text-align: left; padding-left: 20px !important;}
        .bg-navy { background-color: #1a237e; } .bg-red { background-color: #ff5252; } .bg-blue { background-color: #448aff; } .bg-lightblue { background-color: #4fc3f7; }
        
        /* Estilos Chat */
        .chat-box { height: 300px; overflow-y: auto; background: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 10px; }
        .chat-msg { margin-bottom: 10px; padding: 10px; border-radius: 8px; background-color: #e3f2fd; border-left: 4px solid #1976d2;}
        .chat-msg.admin { background-color: #fff3e0; border-left: 4px solid #f57c00; }
        .chat-msg.docente { background-color: #e8f5e9; border-left: 4px solid #388e3c; }
        .msg-privado-enviado { background-color: #f1f8e9; border-right: 4px solid #8bc34a; text-align: right; margin-bottom:10px; padding:10px; border-radius:8px;}
        .msg-privado-recibido { background-color: #fff8e1; border-left: 4px solid #ffb300; margin-bottom:10px; padding:10px; border-radius:8px;}
    </style>
</head>
<body>
    {% if not user %}
    <!-- LOGIN -->
    <div class="container d-flex justify-content-center align-items-center" style="height: 100vh;">
        <div class="card shadow-lg p-5 text-center" style="border-radius: 20px; width: 350px;">
            <h1 class="logo-text">TEC AZUAY</h1>
            <p class="sub-logo mb-4">Instituto Universitario</p>
            {% with messages = get_flashed_messages() %}{% if messages %}<div class="alert alert-danger">{{ messages[0] }}</div>{% endif %}{% endwith %}
            <form method="POST" action="/">
                <input type="text" name="username" class="form-control mb-3" placeholder="Usuario" required>
                <input type="password" name="password" class="form-control mb-3" placeholder="Contraseña" required>
                <button type="submit" class="btn btn-primary w-100 btn-calendario border-0">Ingresar</button>
            </form>
        </div>
    </div>
    {% else %}
    <!-- DASHBOARD -->
    <div class="container mt-4">
        <!-- HEADER -->
        <div class="top-card d-flex justify-content-between align-items-center">
            <div>
                <h1 class="logo-text">TEC AZUAY</h1>
                <p class="sub-logo">Instituto Universitario</p>
                <div style="width: 50px; height: 3px; background-color: #ffc107; margin-top: 5px;"></div>
            </div>
            <div class="d-flex align-items-center">
                <span class="me-3 fw-bold" style="color: #1a237e;"><i class="fa-solid fa-user-tie"></i> {{ user.username }} ({{ user.role }})</span>
                <a href="/logout" class="btn btn-danger rounded-pill px-4 fw-bold shadow-sm">Cerrar Sesión</a>
            </div>
        </div>

        <!-- NAVEGACIÓN FUNCIONAL (TABS) -->
        <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link btn-calendario active" data-bs-toggle="pill" data-bs-target="#pane-calendario"><i class="fa-solid fa-calendar-days me-2"></i> Calendario</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link btn-tareas" data-bs-toggle="pill" data-bs-target="#pane-tareas"><i class="fa-solid fa-book-open me-2"></i> Gestión Académica (Tareas)</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link btn-mensajes" data-bs-toggle="pill" data-bs-target="#pane-mensajes"><i class="fa-solid fa-comments me-2"></i> Mensajería (Foro y Privado)</button>
            </li>
            {% if user.role == 'Administrador' %}
            <li class="nav-item" role="presentation">
                <button class="nav-link btn-admin" data-bs-toggle="pill" data-bs-target="#pane-admin"><i class="fa-solid fa-gears me-2"></i> Administración</button>
            </li>
            {% endif %}
        </ul>

        <div class="welcome-banner shadow-sm">¡Bienvenido, {{ user.username }}! 📚</div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible shadow-sm">
                        {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- CONTENIDO DE LAS PESTAÑAS -->
        <div class="tab-content">
            
            <!-- 1. CALENDARIO -->
            <div class="tab-pane fade show active" id="pane-calendario">
                <div class="card-custom">
                    <h4 class="mb-4" style="color: #1a237e; font-weight: bold;"><i class="fa-regular fa-calendar-days me-2"></i> Horario de Clases Oficial</h4>
                    <div class="table-responsive">
                        <table class="table-schedule">
                            <thead>
                                <tr>
                                    <th style="background: transparent;"></th>
                                    <th>17:00 - 18:00</th>
                                    <th>18:00 - 19:00</th>
                                    <th>19:00 - 20:00</th>
                                    <th>20:00 - 21:00</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td class="day-header">LUNES</td>
                                    <td class="bg-navy">TSCSSS - HACKEO ETICO<br><small>BORIS SQUILANDA</small></td>
                                    <td class="bg-navy">TSCSSS - HACKEO ETICO<br><small>BORIS SQUILANDA</small></td>
                                    <td class="bg-red">CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO</small></td>
                                    <td class="bg-red">CIBERSEGURIDAD EN LA NUBE<br><small>LUIS PORTOCARRERO</small></td>
                                </tr>
                                <tr>
                                    <td class="day-header">MARTES</td>
                                    <td class="bg-blue">CIBERSEGURIDAD Y SISTEMAS<br><small>SHIRLEY TORRES</small></td>
                                    <td class="bg-navy">TSCSSS - HACKEO ETICO<br><small>BORIS SQUILANDA</small></td>
                                    <td class="bg-blue">CIBERSEGURIDAD Y SISTEMAS<br><small>SHIRLEY TORRES</small></td>
                                    <td class="bg-lightblue">CONTINUIDAD DEL NEGOCIO<br><small>SHIRLEY TORRES</small></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 2. GESTIÓN ACADÉMICA (TAREAS Y ARCHIVOS) -->
            <div class="tab-pane fade" id="pane-tareas">
                {% if user.role == 'Estudiante' %}
                <div class="row">
                    <div class="col-md-5">
                        <div class="card-custom mb-4">
                            <h5 style="color: #ff9800; font-weight: bold;"><i class="fa-solid fa-upload"></i> Enviar Trabajo (Sube tu archivo)</h5>
                            <hr>
                            <form action="/submit_task" method="POST" enctype="multipart/form-data">
                                <div class="mb-3">
                                    <label class="form-label fw-bold small">Selecciona la Materia:</label>
                                    <select name="materia" class="form-select" required>
                                        <option value="Hacking Ético">Hacking Ético (Prof. Timoteo)</option>
                                        <option value="Defensa Perimetral">Defensa Perimetral (Prof. Edisson)</option>
                                        <option value="Arquitecturas Cloud">Arquitecturas Cloud (Prof. Admin)</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label fw-bold small">Adjuntar Documento (PDF/PNG):</label>
                                    <input type="file" name="archivo" class="form-control" required>
                                </div>
                                <button type="submit" class="btn text-white w-100 fw-bold" style="background:#ff9800;">Enviar Tarea al Docente</button>
                            </form>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div class="card-custom">
                            <h5 style="color: #1a237e; font-weight: bold;"><i class="fa-solid fa-chart-line"></i> Mi Historial de Calificaciones</h5>
                            <hr>
                            <table class="table table-hover align-middle">
                                <thead class="table-light"><tr><th>Materia</th><th>Documento</th><th>Estado</th><th>Nota</th><th>Retroalimentación</th></tr></thead>
                                <tbody>
                                    {% for t in tareas %}
                                    <tr>
                                        <td>{{ t.materia }}<br><small class="text-muted">{{ t.fecha }}</small></td>
                                        <td><a href="/download/{{ t.archivo_nombre }}" target="_blank" class="badge bg-primary text-decoration-none"><i class="fa-solid fa-paperclip"></i> Ver</a></td>
                                        <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                        <td><strong class="{% if t.nota and t.nota <= 7 %}text-danger{% else %}text-success{% endif %}">{{ t.nota if t.nota else '-' }}/10</strong></td>
                                        <td><small class="text-muted">{{ t.feedback if t.feedback else 'Sin revisión' }}</small></td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="5" class="text-center text-muted p-4">Aún no has enviado tareas.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {% elif user.role == 'Docente' or user.role == 'Administrador' %}
                <div class="card-custom">
                    <h5 style="color: #ff9800; font-weight: bold;"><i class="fa-solid fa-check-double"></i> Bandeja de Calificaciones (Descargar y Calificar)</h5>
                    <hr>
                    <div class="table-responsive">
                        <table class="table table-striped align-middle">
                            <thead class="table-dark"><tr><th>Estudiante</th><th>Materia / Fecha</th><th>Archivo Adjunto</th><th>Estado</th><th>Nota (0-10)</th><th>Observaciones (Requerido <= 7)</th><th>Acción</th></tr></thead>
                            <tbody>
                                {% for t in todas_tareas %}
                                <tr>
                                    <form action="/grade_task" method="POST">
                                        <input type="hidden" name="tarea_id" value="{{ t.id }}">
                                        <td><strong><i class="fa-solid fa-user-graduate text-secondary"></i> {{ t.estudiante_nombre }}</strong></td>
                                        <td>{{ t.materia }}<br><small class="text-muted">{{ t.fecha }}</small></td>
                                        <td><a href="/download/{{ t.archivo_nombre }}" target="_blank" class="btn btn-sm btn-outline-primary"><i class="fa-solid fa-download"></i> Bajar PDF</a></td>
                                        <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                        <td style="width: 90px;"><input type="number" name="nota" class="form-control form-control-sm" min="0" max="10" value="{{ t.nota if t.nota else '' }}" required></td>
                                        <td><input type="text" name="feedback" class="form-control form-control-sm" value="{{ t.feedback if t.feedback else '' }}"></td>
                                        <td><button type="submit" class="btn btn-sm text-white fw-bold" style="background:#ff9800;">Guardar</button></td>
                                    </form>
                                </tr>
                                {% else %}
                                <tr><td colspan="7" class="text-center p-4 text-muted">No hay entregas pendientes de revisión.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- 3. MENSAJERÍA -->
            <div class="tab-pane fade" id="pane-mensajes">
                <div class="row">
                    <!-- CHAT GENERAL -->
                    <div class="col-md-6 mb-4">
                        <div class="card-custom">
                            <h5 style="color: #2196f3; font-weight: bold;"><i class="fa-solid fa-users"></i> Foro Institucional Público</h5>
                            <hr>
                            <div class="chat-box mb-3" id="chatbox">
                                {% for m in mensajes %}
                                <div class="chat-msg {% if m.rol_autor == 'Administrador' %}admin{% elif m.rol_autor == 'Docente' %}docente{% endif %}">
                                    <div class="d-flex justify-content-between mb-1">
                                        <strong>{{ m.autor }} <span class="badge bg-secondary badge-role">{{ m.rol_autor }}</span></strong>
                                        <small class="text-muted" style="font-size: 0.75em;">{{ m.fecha }}</small>
                                    </div>
                                    <div>{{ m.texto }}</div>
                                </div>
                                {% endfor %}
                            </div>
                            <form action="/send_msg" method="POST" class="d-flex">
                                <input type="text" name="mensaje" class="form-control me-2" placeholder="Escribe un mensaje al grupo..." required autocomplete="off">
                                <button type="submit" class="btn btn-primary" style="background:#2196f3; border:none;"><i class="fa-solid fa-paper-plane"></i></button>
                            </form>
                        </div>
                    </div>
                    
                    <!-- MENSAJES PRIVADOS -->
                    <div class="col-md-6">
                        <div class="card-custom">
                            <h5 style="color: #2196f3; font-weight: bold;"><i class="fa-solid fa-envelope"></i> Mensajería Directa</h5>
                            <hr>
                            <!-- Nuevo Mensaje -->
                            <form action="/send_private" method="POST" class="mb-3 p-3 bg-light rounded border">
                                <label class="form-label fw-bold small">Destinatario:</label>
                                <select name="destinatario_id" class="form-select form-select-sm mb-2" required>
                                    <option value="" disabled selected>Selecciona un usuario...</option>
                                    {% for u in all_users %}{% if u.id != user.id %}<option value="{{ u.id }}">{{ u.username }} ({{ u.role }})</option>{% endif %}{% endfor %}
                                </select>
                                <input type="text" name="texto" class="form-control form-control-sm mb-2" placeholder="Escribe tu mensaje privado..." required>
                                <button type="submit" class="btn btn-sm btn-dark w-100">Enviar Privado</button>
                            </form>
                            <!-- Bandeja -->
                            <div style="height: 250px; overflow-y: auto;" class="border p-2 rounded">
                                {% for mp in mensajes_privados %}
                                    {% if mp.remitente_id == user.id %}
                                        <div class="msg-privado-enviado shadow-sm">
                                            <small class="text-muted" style="font-size:0.7em;">{{ mp.fecha }} | Tú -> <strong>{{ mp.destinatario_nombre }}</strong></small><br>
                                            <span>{{ mp.texto }}</span>
                                        </div>
                                    {% else %}
                                        <div class="msg-privado-recibido shadow-sm">
                                            <small class="text-muted" style="font-size:0.7em;">{{ mp.fecha }} | <strong>{{ mp.remitente_nombre }}</strong> -> Tú</small><br>
                                            <span>{{ mp.texto }}</span>
                                        </div>
                                    {% endif %}
                                {% else %}
                                    <p class="text-center text-muted mt-4">No tienes conversaciones privadas.</p>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 4. ADMINISTRACIÓN (Solo Admin) -->
            {% if user.role == 'Administrador' %}
            <div class="tab-pane fade" id="pane-admin">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card-custom">
                            <h5 style="color: #e91e63; font-weight: bold;"><i class="fa-solid fa-user-plus"></i> Crear Usuario</h5>
                            <hr>
                            <form action="/add_user" method="POST">
                                <input type="text" name="new_username" class="form-control mb-2" placeholder="Nombre de usuario" required>
                                <input type="password" name="new_password" class="form-control mb-2" placeholder="Contraseña segura" required>
                                <select name="new_role" class="form-select mb-3">
                                    <option value="Estudiante">Estudiante</option>
                                    <option value="Docente">Docente</option>
                                    <option value="Administrador">Administrador</option>
                                </select>
                                <button type="submit" class="btn text-white w-100 fw-bold" style="background:#e91e63;">Registrar en BD</button>
                            </form>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card-custom">
                            <h5 style="color: #e91e63; font-weight: bold;"><i class="fa-solid fa-shield-halved"></i> Auditoría y Reseteo de Claves</h5>
                            <hr>
                            <div class="table-responsive">
                                <table class="table table-sm table-striped m-0 align-middle">
                                    <thead class="table-dark"><tr><th>Usuario</th><th>Rol</th><th>Forzar Nueva Contraseña</th></tr></thead>
                                    <tbody>
                                        {% for u in all_users %}
                                        <tr>
                                            <td><strong>{{ u.username }}</strong></td>
                                            <td><span class="badge bg-secondary">{{ u.role }}</span></td>
                                            <td>
                                                <form action="/reset_password" method="POST" class="d-flex m-0">
                                                    <input type="hidden" name="user_id" value="{{ u.id }}">
                                                    <input type="password" name="new_password" class="form-control form-control-sm me-2" placeholder="Nueva clave" required>
                                                    <button type="submit" class="btn btn-sm btn-outline-danger fw-bold"><i class="fa-solid fa-key"></i> Cambiar</button>
                                                </form>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        var chatBox = document.getElementById("chatbox");
        if(chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    </script>
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
    
    all_users = User.query.all() 
    tareas = Tarea.query.filter_by(estudiante_id=user.id).order_by(Tarea.id.desc()).all() if user.role == 'Estudiante' else []
    todas_tareas = Tarea.query.order_by(Tarea.id.desc()).all() if user.role in ['Docente', 'Administrador'] else []
    mensajes = Mensaje.query.order_by(Mensaje.id.asc()).all()
    mensajes_privados = MensajePrivado.query.filter((MensajePrivado.remitente_id == user.id) | (MensajePrivado.destinatario_id == user.id)).order_by(MensajePrivado.id.desc()).all()
    
    return render_template_string(HTML_TEMPLATE, user=user, all_users=all_users, tareas=tareas, todas_tareas=todas_tareas, mensajes=mensajes, mensajes_privados=mensajes_privados)

# NUEVA RUTA INTEGRADA: Subir Tarea CON Archivo
@app.route('/submit_task', methods=['POST'])
@limiter.limit("10 per minute") # Evita que saturen el disco subiendo basura
def submit_task():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    
    file = request.files.get('archivo')
    filename = "Sin_Archivo"
    
    if file and file.filename != '':
        # DEFENSA: Verificar que no sea un script malicioso (.sh, .py, .php)
        if not allowed_file(file.filename):
            flash('Error de Seguridad: Tipo de archivo no permitido. Solo PDF, PNG, JPG o DOCX.', 'error')
            return redirect('/dashboard')
            
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    db.session.add(Tarea(estudiante_id=user.id, estudiante_nombre=user.username, materia=request.form['materia'], archivo_nombre=filename, estado='Enviado para Revisión', fecha=hora_actual))
    db.session.commit()
    flash(f'Tu trabajo fue enviado al docente de forma segura.', 'success')
    return redirect('/dashboard')

@app.route('/download/<filename>')
def download_file(filename):
    if 'user_id' not in session: return redirect('/')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/grade_task', methods=['POST'])
def grade_task():
    if 'user_id' in session and User.query.get(session['user_id']).role in ['Docente', 'Administrador']:
        tarea = Tarea.query.get(request.form['tarea_id'])
        nota = int(request.form['nota'])
        feedback = request.form['feedback'].strip()
        
        if nota <= 7 and not feedback:
            flash(f'Atención: Es obligatorio escribir una retroalimentación para notas <= 7.', 'error')
            return redirect('/dashboard')
            
        tarea.nota = nota
        tarea.feedback = feedback
        tarea.estado = 'Calificado'
        db.session.commit()
        flash(f'Calificación guardada exitosamente.', 'success')
    return redirect('/dashboard')

@app.route('/send_msg', methods=['POST'])
def send_msg():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        db.session.add(Mensaje(autor=user.username, rol_autor=user.role, texto=request.form['mensaje'], fecha=datetime.now().strftime("%d/%m/%Y %H:%M")))
        db.session.commit()
    return redirect('/dashboard')

@app.route('/send_private', methods=['POST'])
def send_private():
    if 'user_id' in session:
        remitente = User.query.get(session['user_id'])
        destinatario = User.query.get(request.form['destinatario_id'])
        db.session.add(MensajePrivado(remitente_id=remitente.id, remitente_nombre=remitente.username, destinatario_id=destinatario.id, destinatario_nombre=destinatario.username, texto=request.form['texto'], fecha=datetime.now().strftime("%d/%m/%Y %H:%M")))
        db.session.commit()
        flash(f'Mensaje privado enviado.', 'success')
    return redirect('/dashboard')

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' in session and User.query.get(session['user_id']).role == 'Administrador':
        nuevo_user = request.form['new_username']
        if User.query.filter_by(username=nuevo_user).first():
            flash(f'Error: El usuario ya existe.', 'error')
        else:
            db.session.add(User(username=nuevo_user, password_hash=generate_password_hash(request.form['new_password']), role=request.form['new_role']))
            db.session.commit()
            flash(f'Usuario {nuevo_user} creado con éxito.', 'success')
    return redirect('/dashboard')

@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'user_id' in session and User.query.get(session['user_id']).role == 'Administrador':
        target = User.query.get(request.form['user_id'])
        if target:
            target.password_hash = generate_password_hash(request.form['new_password'])
            db.session.commit()
            flash(f'Contraseña actualizada para {target.username}.', 'success')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)