#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
import signal
import threading
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

def check_gpu():
    """Check if GPU is available and configured"""
    try:
        output = subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT)
        print("✅ GPU detected:")
        # Display a simplified GPU info
        gpu_info = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'],
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
        print(f"   {gpu_info}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ GPU not detected or NVIDIA drivers not installed")
        print("   System will run on CPU only (slower)")
        return False

def check_ollama():
    """Check if Ollama is running and the model is available"""
    from shared.config import OLLAMA_MODEL  # Add this import
    
    try:
        output = subprocess.check_output(['curl', '-s', 'http://localhost:11434/api/tags'], 
                                        stderr=subprocess.STDOUT).decode('utf-8')
        if OLLAMA_MODEL in output:  # Check for configured model instead of hardcoded
            print(f"✅ Ollama running with {OLLAMA_MODEL} model")
            return True
        else:
            print(f"⚠️ Ollama running but {OLLAMA_MODEL} model not found")
            print(f"   Run: ollama pull {OLLAMA_MODEL}")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama not running")
        print("   Start Ollama with: ollama serve")
        return False

def check_rabbitmq():
    """Check if RabbitMQ is running"""
    # Use the port from environment
    management_port = os.getenv('RABBITMQ_MANAGEMENT_PORT', '15672')
    
    try:
        output = subprocess.check_output(
            ['curl', '-s', f'http://localhost:{management_port}/api/overview'], 
            stderr=subprocess.STDOUT).decode('utf-8')
        if "management_version" in output:
            print("✅ RabbitMQ running")
            return True
        else:
            # Try basic connection check if management interface doesn't respond
            try:
                import pika
                from shared.config import RABBITMQ_HOST, RABBITMQ_PORT
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=RABBITMQ_HOST, 
                    port=int(RABBITMQ_PORT)
                ))
                connection.close()
                print("✅ RabbitMQ running (management interface not available)")
                return True
            except Exception as e:
                print(f"❌ RabbitMQ connection failed: {e}")
                return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try another method
        try:
            # Try basic connection check
            import pika
            from shared.config import RABBITMQ_HOST, RABBITMQ_PORT
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=RABBITMQ_HOST, 
                port=int(RABBITMQ_PORT)
            ))
            connection.close()
            print("✅ RabbitMQ running (management interface not available)")
            return True
        except Exception as e:
            print(f"❌ RabbitMQ connection failed: {e}")
            print("   Start RabbitMQ or use Docker: docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management")
            return False

def start_api():
    """Start the API server"""
    print("\n🚀 Starting API server...")
    api_process = subprocess.Popen([sys.executable, API_PATH])
    processes.append(api_process)
    print(f"✅ API server running (PID: {api_process.pid})")
    print(f"   Access at: http://localhost:{os.getenv('PORT', '5000')}")
    return api_process

def start_worker(worker_id=1):
    """Start a worker process"""
    print(f"\n🚀 Starting Worker {worker_id}...")
    worker_process = subprocess.Popen([sys.executable, WORKER_PATH])
    processes.append(worker_process)
    print(f"✅ Worker {worker_id} running (PID: {worker_process.pid})")
    return worker_process

def stop_all_processes():
    """Stop all running processes"""
    print("\n🛑 Stopping all processes...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                process.send_signal(signal.SIGINT)
                print(f"  Sent interrupt signal to process {process.pid}")
                # Give the process some time to shutdown gracefully
                for _ in range(5):  # Wait up to 5 seconds
                    if process.poll() is not None:
                        break
                    time.sleep(1)
                # Force kill if still running
                if process.poll() is None:
                    process.terminate()
                    print(f"  Terminated process {process.pid}")
            except Exception as e:
                print(f"  Error stopping process {process.pid}: {e}")

def monitor_processes():
    """Monitor running processes and restart if they crash"""
    while True:
        for i, process in enumerate(processes[:]):
            if process.poll() is not None:
                print(f"⚠️ Process {process.pid} has crashed with code {process.returncode}")
                # Remove the dead process
                processes.remove(process)
                # Determine process type and restart
                if WORKER_PATH in ' '.join(process.args):
                    print("🔄 Restarting worker...")
                    worker_id = next((i for i, arg in enumerate(process.args) if '--worker-id' in arg), None)
                    if worker_id:
                        worker_id = int(process.args[worker_id + 1])
                    else:
                        worker_id = 1
                    processes.append(start_worker(worker_id))
                elif API_PATH in ' '.join(process.args):
                    print("🔄 Restarting API server...")
                    processes.append(start_api())
        time.sleep(5)  # Check every 5 seconds

def parse_arguments():
    parser = argparse.ArgumentParser(description="OCR System Launcher")
    parser.add_argument("--all", action="store_true", help="Start all services")
    parser.add_argument("--api", action="store_true", help="Start API server only")
    parser.add_argument("--worker", action="store_true", help="Start worker only")
    parser.add_argument("--monitor", action="store_true", help="Monitor processes")
    parser.add_argument("--model", type=str, help="Override the Ollama model to use")
    return parser.parse_args()

def main():
    parser = argparse.ArgumentParser(description="Run OCR API and Workers")
    
    parser.add_argument('--api', action='store_true', help='Start the API server')
    parser.add_argument('--worker', action='store_true', help='Start a worker')
    parser.add_argument('--all', action='store_true', help='Start both API and worker')
    parser.add_argument('--workers', type=int, default=1, help='Number of workers to start')
    parser.add_argument('--monitor', action='store_true', help='Monitor and restart processes if they crash')
    parser.add_argument('--check', action='store_true', help='Check dependencies and exit')
    
    args = parser.parse_args()
    
    # Show banner
    print("\n" + "="*50)
    print("           OCR SYSTEM LAUNCHER")
    print("="*50)
    
    # Check dependencies
    gpu_available = check_gpu()
    ollama_running = check_ollama()
    rabbitmq_running = check_rabbitmq()
    
    # If only checking dependencies, exit here
    if args.check:
        sys.exit(0)
    
    # Warn if dependencies aren't met
    if not (ollama_running and rabbitmq_running):
        print("\n⚠️ Some required services are not running!")
        choice = input("Continue anyway? (y/n): ").lower()
        if choice != 'y':
            print("Exiting.")
            sys.exit(1)
    
    # Start requested components
    try:
        if args.api or args.all:
            start_api()
        
        num_workers = args.workers if args.worker or args.all else 0
        for i in range(1, num_workers + 1):
            start_worker(i)
        
        if not processes:
            parser.print_help()
            sys.exit(1)
        
        if args.monitor:
            print("\n👀 Process monitoring enabled")
            monitor_thread = threading.Thread(target=monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
        
        print("\n⌛ Press Ctrl+C to stop all processes...")
        
        # Wait for KeyboardInterrupt
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⛔ Received keyboard interrupt")
    finally:
        stop_all_processes()
        print("\n✨ OCR system stopped")

if __name__ == "__main__":
    args = parse_arguments()

    # Set model environment variable directly if specified
    if args.model:
        print(f"🔄 Setting model: {args.model}")
        os.environ["OLLAMA_MODEL"] = args.model
    
    main()