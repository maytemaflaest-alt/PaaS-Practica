from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def inicio():
    # Simulamos la lectura de una credencial segura desde el PaaS
    llave_secreta = os.environ.get('SECRET_KEY', 'ALERTA: Entorno Inseguro - Clave no configurada')
    return f"<h1>Aplicación PaaS Desplegada Correctamente</h1><p>Estado de seguridad: {llave_secreta}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)