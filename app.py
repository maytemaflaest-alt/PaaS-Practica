from flask import Flask, request, render_template_string, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_segura_v2')

# USAMOS UNA NUEVA BD PARA SOPORTAR EL CHAT Y LAS NOTAS
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_v2.db'
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

with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('AdminSeguro2026!'), role='Administrador'))
        db.session.add(User(username='alumno', password_hash=generate_password_hash('Estudiante#1'), role='Estudiante'))
        db.session.add(User(username='profesor', password_hash=generate_password_hash('ProfeCyber24'), role='Docente'))
        db.session.commit()

# --- VISTAS HTML (CON BOOTSTRAP 5 PARA DISEÑO PROFESIONAL) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Campus Virtual - TEC AZUAY</title>
    <!-- CSS Profesional via Bootstrap -->
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
    </style>
</head>
<body>
    {% if not user %}
    <!-- PANTALLA DE LOGIN -->
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
    <!-- DASHBOARD PRINCIPAL -->
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

        <!-- PESTAÑAS DE NAVEGACIÓN -->
        <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
            <li class="nav-item">
                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#academico"><i class="fa-solid fa-book me-1"></i> Panel Académico</button>
            </li>
            <li class="nav-item">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#foro"><i class="fa-regular fa-comments me-1"></i> Foro de Mensajería</button>
            </li>
            {% if user.role == 'Administrador' %}
            <li class="nav-item">
                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#admin"><i class="fa-solid fa-gears me-1"></i> Administración</button>
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
                                    <div><strong>Hacking Ético</strong><br><small class="text-muted">Prof. Timoteo</small></div>
                                    <form action="/submit_task" method="POST"><input type="hidden" name="materia" value="Hacking Ético"><button class="btn btn-sm btn-success">Entregar Trabajo</button></form>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <div><strong>Defensa Perimetral</strong><br><small class="text-muted">Prof. Edisson</small></div>
                                    <form action="/submit_task" method="POST"><input type="hidden" name="materia" value="Defensa Perimetral"><button class="btn btn-sm btn-success">Entregar Trabajo</button></form>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <div><strong>Arquitecturas Cloud</strong><br><small class="text-muted">Prof. Admin</small></div>
                                    <form action="/submit_task" method="POST"><input type="hidden" name="materia" value="Arquitecturas Cloud"><button class="btn btn-sm btn-success">Entregar Trabajo</button></form>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div class="card shadow-sm">
                            <div class="card-header bg-primary text-white fw-bold">Mi Historial de Calificaciones</div>
                            <div class="card-body p-0">
                                <table class="table table-hover m-0">
                                    <thead class="table-light"><tr><th>Materia</th><th>Estado</th><th>Nota</th><th>Retroalimentación del Docente</th></tr></thead>
                                    <tbody>
                                        {% for t in tareas %}
                                        <tr>
                                            <td>{{ t.materia }}</td>
                                            <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                            <td><strong class="{% if t.nota and t.nota <= 7 %}text-danger{% else %}text-success{% endif %}">{{ t.nota if t.nota else '-' }}/10</strong></td>
                                            <td><small class="text-muted">{{ t.feedback if t.feedback else 'Sin comentarios aún.' }}</small></td>
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
                    <div class="card-header bg-success text-white fw-bold">Centro de Calificaciones (Entregas Pendientes)</div>
                    <div class="card-body p-0 table-responsive">
                        <table class="table table-striped m-0 align-middle">
                            <thead class="table-dark"><tr><th>Estudiante</th><th>Materia</th><th>Estado</th><th>Calificar (Sobre 10)</th><th>Observaciones (Obligatorio si Nota <= 7)</th><th>Acción</th></tr></thead>
                            <tbody>
                                {% for t in todas_tareas %}
                                <tr>
                                    <form action="/grade_task" method="POST">
                                        <input type="hidden" name="tarea_id" value="{{ t.id }}">
                                        <td><strong><i class="fa-solid fa-user-graduate text-secondary"></i> {{ t.estudiante_nombre }}</strong></td>
                                        <td>{{ t.materia }}</td>
                                        <td><span class="badge bg-{{ 'success' if t.estado == 'Calificado' else 'warning text-dark' }}">{{ t.estado }}</span></td>
                                        <td style="width: 120px;">
                                            <input type="number" name="nota" class="form-control form-control-sm" min="0" max="10" value="{{ t.nota if t.nota else '' }}" required>
                                        </td>
                                        <td>
                                            <input type="text" name="feedback" class="form-control form-control-sm" placeholder="Escribe tu retroalimentación..." value="{{ t.feedback if t.feedback else '' }}">
                                        </td>
                                        <td><button type="submit" class="btn btn-sm btn-primary"><i class="fa-solid fa-floppy-disk"></i> Guardar</button></td>
                                    </form>
                                </tr>
                                {% else %}
                                <tr><td colspan="6" class="text-center p-4 text-muted">No hay entregas registradas en el sistema.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- TAB: FORO / CHAT -->
            <div class="tab-pane fade" id="foro">
                <div class="card shadow-sm">
                    <div class="card-header card-header-custom d-flex justify-content-between">
                        <span>Foro Institucional General</span>
                        <span class="badge bg-light text-dark"><i class="fa-solid fa-circle text-success" style="font-size: 8px;"></i> Online</span>
                    </div>
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
                            {% else %}
                            <p class="text-center text-muted mt-5">No hay mensajes aún. ¡Sé el primero en saludar!</p>
                            {% endfor %}
                        </div>
                        <form action="/send_msg" method="POST" class="d-flex">
                            <input type="text" name="mensaje" class="form-control me-2" placeholder="Escribe un mensaje al grupo..." required autocomplete="off">
                            <button type="submit" class="btn btn-primary"><i class="fa-solid fa-paper-plane"></i> Enviar</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- TAB: ADMINISTRADOR -->
            {% if user.role == 'Administrador' %}
            <div class="tab-pane fade" id="admin">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white">Nuevo Usuario</div>
                            <div class="card-body">
                                <form action="/add_user" method="POST">
                                    <div class="mb-2"><input type="text" name="new_username" class="form-control" placeholder="Nombre de usuario" required></div>
                                    <div class="mb-2"><input type="password" name="new_password" class="form-control" placeholder="Contraseña" required></div>
                                    <div class="mb-3">
                                        <select name="new_role" class="form-select">
                                            <option value="Estudiante">Estudiante</option>
                                            <option value="Docente">Docente</option>
                                            <option value="Administrador">Administrador</option>
                                        </select>
                                    </div>
                                    <button type="submit" class="btn btn-success w-100"><i class="fa-solid fa-user-plus"></i> Registrar</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card shadow-sm">
                            <div class="card-header bg-dark text-white">Directorio de Usuarios</div>
                            <table class="table table-sm table-striped m-0">
                                <thead><tr><th>ID</th><th>Usuario</th><th>Rol</th><th>Contraseña Cifrada (SHA256)</th></tr></thead>
                                <tbody>
                                    {% for u in all_users %}
                                    <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td><span class="badge bg-secondary">{{ u.role }}</span></td><td style="font-size:10px; color:#999; font-family:monospace;">{{ u.password_hash[:40] }}...</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <!-- Scripts de Bootstrap para pestañas y alertas -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-scroll del chat al fondo
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
        flash('Credenciales incorrectas o usuario no registrado.', 'error')
    return render_template_string(HTML_TEMPLATE, user=None)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/')
    user = User.query.get(session['user_id'])
    
    all_users = User.query.all() if user.role == 'Administrador' else []
    tareas = Tarea.query.filter_by(estudiante_id=user.id).all() if user.role == 'Estudiante' else []
    todas_tareas = Tarea.query.all() if user.role in ['Docente', 'Administrador'] else []
    mensajes = Mensaje.query.order_by(Mensaje.id.asc()).all()
    
    return render_template_string(HTML_TEMPLATE, user=user, all_users=all_users, tareas=tareas, todas_tareas=todas_tareas, mensajes=mensajes)

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

@app.route('/submit_task', methods=['POST'])
def submit_task():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        db.session.add(Tarea(estudiante_id=user.id, estudiante_nombre=user.username, materia=request.form['materia'], estado='Enviado para Revisión'))
        db.session.commit()
        flash(f'Tu trabajo de {request.form["materia"]} fue enviado al docente.', 'success')
    return redirect('/dashboard')

@app.route('/grade_task', methods=['POST'])
def grade_task():
    if 'user_id' in session and User.query.get(session['user_id']).role in ['Docente', 'Administrador']:
        tarea = Tarea.query.get(request.form['tarea_id'])
        nota = int(request.form['nota'])
        feedback = request.form['feedback'].strip()
        
        # LÓGICA EXIGIDA: Si la nota es <= 7, el feedback es obligatorio
        if nota <= 7 and not feedback:
            flash(f'Atención: No se guardó la calificación del alumno {tarea.estudiante_nombre}. Es obligatorio escribir una retroalimentación/recomendación para notas menores o iguales a 7.', 'error')
            return redirect('/dashboard')
            
        tarea.nota = nota
        tarea.feedback = feedback
        tarea.estado = 'Calificado'
        db.session.commit()
        flash(f'Calificación guardada y publicada para el estudiante {tarea.estudiante_nombre}.', 'success')
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