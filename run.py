# !/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
import signal
import threading
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_PATH = os.path.join(BASE_DIR, 'api', 'app.py')
WORKER_PATH = os.path.join(BASE_DIR, 'worker', 'ocr_worker.py')
UPLOAD_DIR = os.path.join(BASE_DIR, 'data', 'uploads')
RESULTS_DIR = os.path.join(BASE_DIR, 'data', 'resultados')

# Create required directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Global variables to track running processes
processes = []


def is_port_in_use(port):
    """Verifica si un puerto está en uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_free_port():
    """Encuentra un puerto libre disponible"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def verify_ollama_model():
    """Verifica que el modelo Ollama qwen2.5vl:7b esté disponible"""
    print("Verificando disponibilidad del modelo qwen2.5vl:7b...")
    try:
        # Verificar si el modelo está disponible
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'qwen2.5vl:7b' not in result.stdout:
            print("⚠️ Modelo qwen2.5vl:7b no encontrado, descargando...")
            subprocess.run(['ollama', 'pull', 'qwen2.5vl:7b'], check=True)
            print("✅ Modelo qwen2.5vl:7b descargado correctamente")
        else:
            print("✅ Modelo qwen2.5vl:7b ya está disponible")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Error al verificar/descargar el modelo: {e}")
        return False


def start_api():
    """Start the API server"""
    print("\n🚀 Iniciando servidor API...")

    # Verificar si el puerto 5000 está disponible
    if is_port_in_use(5000):
        # Si el puerto 5000 está ocupado, encontrar un puerto libre
        port = find_free_port()
        print(f"⚠️ El puerto 5000 está en uso. Usando puerto alternativo: {port}")
        os.environ['PORT'] = str(port)
    else:
        port = 5000
        os.environ['PORT'] = '5000'

    # Iniciar el proceso API
    api_process = subprocess.Popen([sys.executable, API_PATH])
    processes.append(api_process)
    print(f"✅ Servidor API funcionando (PID: {api_process.pid})")
    print(f"   Acceder en: http://localhost:{port}")
    return api_process


def start_worker():
    """Inicia un proceso worker para procesar las imágenes"""
    print("\n🚀 Iniciando Worker OCR...")
    # Iniciar el proceso worker
    worker_process = subprocess.Popen([sys.executable, WORKER_PATH])
    processes.append(worker_process)
    print(f"✅ Worker OCR funcionando (PID: {worker_process.pid})")
    return worker_process


def stop_all_processes():
    """Stop all running processes"""
    print("\n🛑 Deteniendo todos los procesos...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                process.send_signal(signal.SIGINT)
                print(f"  Enviada señal de interrupción al proceso {process.pid}")
                # Give the process some time to shutdown gracefully
                for _ in range(5):  # Wait up to 5 seconds
                    if process.poll() is not None:
                        break
                    time.sleep(1)
                # Force kill if still running
                if process.poll() is None:
                    process.terminate()
                    print(f"  Proceso {process.pid} terminado")
            except Exception as e:
                print(f"  Error al detener el proceso {process.pid}: {e}")


def main():
    # Mostrar banner
    print("\n" + "=" * 50)
    print("           SISTEMA OCR INICIANDO")
    print("=" * 50)

    # Verificar el modelo Ollama
    if not verify_ollama_model():
        print("\n⚠️ No se pudo verificar el modelo Ollama!")
        choice = input("¿Continuar de todos modos? (s/n): ").lower()
        if choice != 's':
            print("Saliendo.")
            sys.exit(1)

    # Iniciar API y Worker
    try:
        start_api()
        # Iniciar el worker para procesar las imágenes
        start_worker()

        print("\n⌛ Presiona Ctrl+C para detener el servidor...")

        # Esperar por KeyboardInterrupt
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n⛔ Señal de interrupción recibida")
    finally:
        stop_all_processes()
        print("\n✨ Sistema OCR detenido")


if __name__ == "__main__":
    main()