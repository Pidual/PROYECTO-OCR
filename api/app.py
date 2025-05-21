import sys  # Se asegura de importar sys al inicio
import os
import json
import uuid
import base64
import pika
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Añadir directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__,
    template_folder='../templates',  # Ruta relativa a las plantillas
    static_folder='../static'        # Ruta relativa a los archivos estáticos
)


# Crear directorios necesarios
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'resultados')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


# Conexión a RabbitMQ
def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=os.getenv('RABBITMQ_HOST', 'localhost'),
        port=int(os.getenv('RABBITMQ_PORT', 5672))
    ))


# Endpoint: Procesar imagen
@app.route('/procesar-imagen', methods=['POST'])
def process_image():
    job_id = str(uuid.uuid4())

    if 'image' in request.files:
        # Si la imagen llega como un archivo
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó un archivo"}), 400

        filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}{os.path.splitext(file.filename)[1]}")
        file.save(filename)
    elif request.is_json and 'image_base64' in request.json:
        # Si la imagen llega en formato base64
        try:
            image_data = base64.b64decode(request.json['image_base64'])
            filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}.png")
            with open(filename, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Imagen base64 inválida: {str(e)}"}), 400
    else:
        return jsonify({"error": "No se proporcionó ninguna imagen"}), 400

    # Publica el trabajo en RabbitMQ
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='ocr_queue', durable=True)

        message = {
            "job_id": job_id,
            "filename": filename
        }
        channel.basic_publish(
            exchange='',
            routing_key='ocr_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Mensaje persistente
            )
        )
        connection.close()
        return jsonify({"job_id": job_id, "status": "enviado"})
    except Exception as e:
        return jsonify({"error": f"No se pudo enviar el trabajo: {str(e)}"}), 500


# Endpoint: Obtener resultado
@app.route('/resultado/<job_id>', methods=['GET'])
def get_result(job_id):
    try:
        uuid.UUID(job_id, version=4)  # Valida el formato del job_id
    except ValueError:
        return jsonify({"error": "Formato de ID de trabajo inválido"}), 400

    result_file = os.path.join(RESULT_FOLDER, f"{job_id}.json")

    if os.path.exists(result_file):
        try:
            with open(result_file, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": f"No se pudo leer el archivo de resultado: {str(e)}"}), 500
    else:
        return jsonify({"status": "procesando"})


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
