from flask import Flask, request, render_template_string, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_segura_v5')

# Usamos V5 para garantizar una base de datos fresca y sin errores
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_v5.db'
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
    nota = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)

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

# --- INICIALIZACIÓN SEGURA (Corrección del error de Edisson y Timoteo) ---
with app.app_context():
    db.create_all()
    # Ahora verificamos UNO POR UNO. Si no existen, se crean. Nunca se perderán.
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('AdminSeguro2026!'), role='Administrador'))
    if not User.query.filter_by(username='alumno').first():
        db.session.add(User(username='alumno', password_hash=generate_password_hash('Estudiante#1'), role='Estudiante'))
    if not User.query.filter_by(username='profesor').first():
        db.session.add(User(username='profesor', password_hash=generate_password_hash('ProfeCyber24'), role='Docente'))
    if not User.query.filter_by(username='Edisson').first():
        db.session.add(User(username='Edisson', password_hash=generate_password_hash('Estudiante2026'), role='Estudiante'))
    if not User.query.filter_by(username='Timoteo').first():
        db.session.add(User(username='Timoteo', password_hash=generate_password_hash('Estudiante2026'), role='Estudiante'))
    db.session.commit()

# --- VISTAS HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Campus Virtual - TEC AZUAY</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f4f6f9; }
        .navbar-custom { background-color: #1a237e; }
        .card-header-custom { background-color: #283593; color: white; font-weight: bold; }
        .chat-box { height: 300px; overflow-y: auto; background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .chat-msg { margin-bottom: 10px; padding: 10px; border-radius: 8px; background-color: #e3f2fd; border-left: 4px solid #1976d2;}
        .chat-msg.admin { background-color: #fff3e0; border-left: 4px solid #f57c00; }
        .chat-msg.docente { background-color: #e8f5e9; border-left: 4px solid #388e3c; }
        .badge-role { font-size: 0.9em; }
        .msg-privado-enviado { background-color: #f1f8e9; border-right: 4px solid #8bc34a; text-align: right; margin-bottom:10px; padding:10px; border-radius:5px;}
        .msg-privado-recibido { background-color: #fff8e1; border-left: 4px solid #ffb300; margin-bottom:10px; padding:10px; border-radius:5px;}
    </style>
</head>
<body>
    {% if not user %}
    <!-- LOGIN -->
    <div class="container d-flex justify-content-center align-items-center" style="height: 100vh;">
        <div class="card shadow-lg" style="width: 25rem;">
            <div class="card-body text-center p-5">
                <i class="fa-solid fa-graduation-cap fa-4x mb-3" style="color: #1a237e;"></i>
                <h3 class="mb-1" style="color: #1a237e; font-weight: bold;">TEC AZUAY</h3>
                <p class="text-muted mb-4">Campus Virtual Interactivo</p>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    {% for category, message in messages %}
                      <div class="alert alert-danger py-2">{{ message }}</div>
                    {% endfor %}
                  {% endif %}
                {% endwith %}
                
                <form method="POST" action="/">
                    <div class="input-group mb-3">
                        <span class="input-group-text"><i class="fa-solid fa-user"></i></span>
                        <input type="text" name="username" class="form-control" placeholder="Usuario" required>
                    </div>
                    <div class="input-group mb-4">
                        <span class="input-group-text"><i class="fa-solid fa-lock"></i></span>
                        <input type="password" name="password" class="form-control" placeholder="Contraseña segura" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100" style="background-color: #1a237e; border:none;">Ingresar al Campus</button>
                </form>
            </div>
        </div>
    </div>
    {% else %}
    <!-- DASHBOARD -->
    <nav class="navbar navbar-expand-lg navbar-dark navbar-custom mb-4 shadow-sm">
        <div class="container">
            <a class="navbar-brand" href="#"><i class="fa-solid fa-graduation-cap me-2"></i> Campus Virtual PaaS</a>
            <div class="d-flex align-items-center text-white">
                <span class="me-3"><i class="fa-solid fa-circle-user me-1"></i> {{ user.username }} ({{ user.role }})</span>
                <a href="/logout" class="btn btn-sm btn-danger"><i class="fa-solid fa-right-from-bracket"></i> Salir</a>
            </div>
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- PESTAÑAS -->
        <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
            <li class="nav-item">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#academico"><i class="fa-solid fa-book me-1"></i> Panel Académico</button>
            </li>
            <li class="nav-item">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#foro"><i class="fa-solid fa-users me-1"></i> Foro General</button>
            </li>
            <li class="nav-item">
                <button class="nav-link text-primary fw-bold" data-bs-toggle="tab" data-bs-target="#chat_privado"><i class="fa-solid fa-envelope me-1"></i> Mensajes Privados</button>
            </li>
            {% if user.role == 'Administrador' %}
            <li class="nav-item">
                <button class="nav-link text-danger fw-bold" data-bs-toggle="tab" data-bs-target="#admin"><i class="fa-solid fa-gears me-1"></i> Administración</button>
            </li>
            {% endif %}
        </ul>

        <div class="tab-content">
            <!-- TAB: PANEL ACADÉMICO -->
            <div class="tab-pane fade show active" id="academico">
                {% if user.role == 'Estudiante' %}
                <div class="row">
                    <div class="col-md-5">
                        <div class="card shadow-sm mb-4">
                            <div class="card-header card-header-custom">Mis Asignaturas</div>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <div><strong>Hacking Ético</strong><br><small class="text-muted">Prof. Admin</small></div>
                                    <form action="/submit_task" method="POST"><input type="hidden" name="materia" value="Hacking Ético"><button class="btn btn-sm btn-success">Entregar</button></form>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <div><strong>Arquitecturas Cloud</strong><br><small class="text-muted">Prof. Docente</small></div>
                                    <form action="/submit_task" method="POST"><input type="hidden" name="materia" value="Arquitecturas Cloud"><button class="btn btn-sm btn-success">Entregar</button></form>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div class="card shadow-sm">
                            <div class="card-header bg-primary text-white fw-bold">Mi Historial de Calificaciones</div>
                            <div class="card-body p-0">
                                <table class="table table-hover m-0">
                                    <thead class="table-light"><tr><th>Materia</th><th>Estado</th><th>Nota</th><th>Retroalimentación</th></tr></thead>
                                    <tbody>
                                        {% for t in tareas %}
                                        <tr>
                                            <td>{{ t.materia }}</td>
                                            <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                            <td><strong class="{% if t.nota and t.nota <= 7 %}text-danger{% else %}text-success{% endif %}">{{ t.nota if t.nota else '-' }}/10</strong></td>
                                            <td><small class="text-muted">{{ t.feedback if t.feedback else 'Sin comentarios.' }}</small></td>
                                        </tr>
                                        {% else %}
                                        <tr><td colspan="4" class="text-center p-3 text-muted">Aún no has enviado tareas.</td></tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                {% elif user.role == 'Docente' or user.role == 'Administrador' %}
                <div class="card shadow-sm">
                    <div class="card-header bg-success text-white fw-bold">Centro de Calificaciones</div>
                    <div class="card-body p-0 table-responsive">
                        <table class="table table-striped m-0 align-middle">
                            <thead class="table-dark"><tr><th>Estudiante</th><th>Materia</th><th>Estado</th><th>Calificar</th><th>Observaciones</th><th>Acción</th></tr></thead>
                            <tbody>
                                {% for t in todas_tareas %}
                                <tr>
                                    <form action="/grade_task" method="POST">
                                        <input type="hidden" name="tarea_id" value="{{ t.id }}">
                                        <td><strong>{{ t.estudiante_nombre }}</strong></td>
                                        <td>{{ t.materia }}</td>
                                        <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                        <td style="width: 100px;"><input type="number" name="nota" class="form-control form-control-sm" min="0" max="10" value="{{ t.nota if t.nota else '' }}" required></td>
                                        <td><input type="text" name="feedback" class="form-control form-control-sm" value="{{ t.feedback if t.feedback else '' }}"></td>
                                        <td><button type="submit" class="btn btn-sm btn-primary">Guardar</button></td>
                                    </form>
                                </tr>
                                {% else %}
                                <tr><td colspan="6" class="text-center p-4 text-muted">No hay entregas.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- TAB: CHAT PRIVADO -->
            <div class="tab-pane fade" id="chat_privado">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card shadow-sm mb-3">
                            <div class="card-header bg-primary text-white"><i class="fa-solid fa-pen-to-square"></i> Nuevo Mensaje Directo</div>
                            <div class="card-body">
                                <form action="/send_private" method="POST">
                                    <div class="mb-3">
                                        <label class="form-label text-muted small">Selecciona a quién escribirle:</label>
                                        <select name="destinatario_id" class="form-select shadow-sm" required>
                                            <option value="" disabled selected>Contactos disponibles...</option>
                                            {% for u in all_users %}
                                                {% if u.id != user.id %}
                                                <option value="{{ u.id }}">{{ u.username }} ({{ u.role }})</option>
                                                {% endif %}
                                            {% endfor %}
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <textarea name="texto" class="form-control shadow-sm" rows="4" placeholder="Escribe tu mensaje privado aquí..." required></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100"><i class="fa-solid fa-paper-plane"></i> Enviar Mensaje</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-8">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white"><i class="fa-solid fa-inbox"></i> Mis Conversaciones Privadas</div>
                            <div class="card-body" style="height: 400px; overflow-y: auto;">
                                {% for mp in mensajes_privados %}
                                    {% if mp.remitente_id == user.id %}
                                        <div class="msg-privado-enviado shadow-sm">
                                            <small class="text-muted" style="font-size:0.7em;">{{ mp.fecha }}</small><br>
                                            <span class="text-muted small">Tú escribiste a <strong>{{ mp.destinatario_nombre }}</strong>:</span><br>
                                            <span>{{ mp.texto }}</span>
                                        </div>
                                    {% else %}
                                        <div class="msg-privado-recibido shadow-sm">
                                            <small class="text-muted" style="font-size:0.7em;">{{ mp.fecha }}</small><br>
                                            <span class="text-muted small"><strong><i class="fa-solid fa-user me-1"></i> {{ mp.remitente_nombre }}</strong> te escribió:</span><br>
                                            <span>{{ mp.texto }}</span>
                                        </div>
                                    {% endif %}
                                {% else %}
                                    <div class="text-center text-muted mt-5">
                                        <i class="fa-solid fa-envelope-open-text fa-3x mb-3"></i>
                                        <p>No tienes mensajes privados aún.</p>
                                    </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB: FORO GENERAL -->
            <div class="tab-pane fade" id="foro">
                <div class="card shadow-sm">
                    <div class="card-header card-header-custom">Foro Institucional General</div>
                    <div class="card-body bg-light">
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
                            <input type="text" name="mensaje" class="form-control me-2" placeholder="Mensaje público..." required autocomplete="off">
                            <button type="submit" class="btn btn-primary">Enviar</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- TAB: ADMIN (CON FUNCIÓN DE RESETEO DE CONTRASEÑAS) -->
            {% if user.role == 'Administrador' %}
            <div class="tab-pane fade" id="admin">
                <div class="row">
                    <!-- CREAR USUARIO -->
                    <div class="col-md-3">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white">Nuevo Usuario</div>
                            <div class="card-body">
                                <form action="/add_user" method="POST">
                                    <div class="mb-2"><input type="text" name="new_username" class="form-control" placeholder="Nombre" required></div>
                                    <div class="mb-2"><input type="password" name="new_password" class="form-control" placeholder="Contraseña" required></div>
                                    <div class="mb-3">
                                        <select name="new_role" class="form-select">
                                            <option value="Estudiante">Estudiante</option>
                                            <option value="Docente">Docente</option>
                                            <option value="Administrador">Administrador</option>
                                        </select>
                                    </div>
                                    <button type="submit" class="btn btn-success w-100">Registrar</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <!-- DIRECTORIO Y GESTIÓN DE CREDENCIALES -->
                    <div class="col-md-9">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white">Directorio y Gestión de Credenciales</div>
                            <div class="table-responsive">
                                <table class="table table-sm table-striped m-0 align-middle">
                                    <thead class="table-light"><tr><th>ID</th><th>Usuario</th><th>Rol</th><th>Cambiar Contraseña</th></tr></thead>
                                    <tbody>
                                        {% for u in all_users %}
                                        <tr>
                                            <td>{{ u.id }}</td>
                                            <td><strong>{{ u.username }}</strong></td>
                                            <td><span class="badge bg-secondary">{{ u.role }}</span></td>
                                            <td>
                                                <form action="/reset_password" method="POST" class="d-flex m-0" style="max-width: 280px;">
                                                    <input type="hidden" name="user_id" value="{{ u.id }}">
                                                    <input type="password" name="new_password" class="form-control form-control-sm me-2" placeholder="Nueva clave" required>
                                                    <button type="submit" class="btn btn-sm btn-warning text-dark fw-bold"><i class="fa-solid fa-key"></i> Actualizar</button>
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
    tareas = Tarea.query.filter_by(estudiante_id=user.id).all() if user.role == 'Estudiante' else []
    todas_tareas = Tarea.query.all() if user.role in ['Docente', 'Administrador'] else []
    mensajes = Mensaje.query.order_by(Mensaje.id.asc()).all()
    
    mensajes_privados = MensajePrivado.query.filter(
        (MensajePrivado.remitente_id == user.id) | (MensajePrivado.destinatario_id == user.id)
    ).order_by(MensajePrivado.id.desc()).all()
    
    return render_template_string(HTML_TEMPLATE, user=user, all_users=all_users, tareas=tareas, todas_tareas=todas_tareas, mensajes=mensajes, mensajes_privados=mensajes_privados)

@app.route('/send_private', methods=['POST'])
def send_private():
    if 'user_id' in session:
        remitente = User.query.get(session['user_id'])
        destinatario = User.query.get(request.form['destinatario_id'])
        hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        db.session.add(MensajePrivado(
            remitente_id=remitente.id, 
            remitente_nombre=remitente.username,
            destinatario_id=destinatario.id, 
            destinatario_nombre=destinatario.username,
            texto=request.form['texto'], 
            fecha=hora_actual
        ))
        db.session.commit()
        flash(f'Mensaje privado enviado a {destinatario.username}.', 'success')
    return redirect('/dashboard')

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' in session and User.query.get(session['user_id']).role == 'Administrador':
        nuevo_user = request.form['new_username']
        if User.query.filter_by(username=nuevo_user).first():
            flash(f'Error: El usuario "{nuevo_user}" ya existe.', 'error')
        else:
            db.session.add(User(username=nuevo_user, password_hash=generate_password_hash(request.form['new_password']), role=request.form['new_role']))
            db.session.commit()
            flash(f'Usuario {nuevo_user} creado con éxito.', 'success')
    return redirect('/dashboard')

# NUEVA RUTA PARA RESTABLECER CONTRASEÑAS DESDE ADMIN
@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'user_id' in session and User.query.get(session['user_id']).role == 'Administrador':
        target_user = User.query.get(request.form['user_id'])
        if target_user:
            target_user.password_hash = generate_password_hash(request.form['new_password'])
            db.session.commit()
            flash(f'¡La contraseña del usuario {target_user.username} ha sido actualizada exitosamente!', 'success')
    return redirect('/dashboard')

@app.route('/submit_task', methods=['POST'])
def submit_task():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        db.session.add(Tarea(estudiante_id=user.id, estudiante_nombre=user.username, materia=request.form['materia'], estado='Enviado para Revisión'))
        db.session.commit()
        flash(f'Tu trabajo de {request.form["materia"]} fue enviado.', 'success')
    return redirect('/dashboard')

@app.route('/grade_task', methods=['POST'])
def grade_task():
    if 'user_id' in session and User.query.get(session['user_id']).role in ['Docente', 'Administrador']:
        tarea = Tarea.query.get(request.form['tarea_id'])
        nota = int(request.form['nota'])
        feedback = request.form['feedback'].strip()
        
        if nota <= 7 and not feedback:
            flash(f'Atención: Es obligatorio escribir una retroalimentación para notas menores o iguales a 7.', 'error')
            return redirect('/dashboard')
            
        tarea.nota = nota
        tarea.feedback = feedback
        tarea.estado = 'Calificado'
        db.session.commit()
        flash(f'Calificación guardada para el estudiante {tarea.estudiante_nombre}.', 'success')
    return redirect('/dashboard')

@app.route('/send_msg', methods=['POST'])
def send_msg():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        db.session.add(Mensaje(autor=user.username, rol_autor=user.role, texto=request.form['mensaje'], fecha=hora_actual))
        db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)