import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base application paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'data', 'uploads')
RESULTS_DIR = os.path.join(BASE_DIR, 'data', 'resultados')

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'ocr_queue')

# Ollama configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api')

# API configuration
API_HOST = os.getenv('HOST', '0.0.0.0')
API_PORT = int(os.getenv('PORT', 5000))
API_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'