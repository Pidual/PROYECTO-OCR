from flask import Flask, render_template

# Importa la instancia del app desde api/app.py
from api.app import app

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
