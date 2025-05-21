import os
import json
import pika
import time
import sys
from dotenv import load_dotenv
from ocr_processor import process_image_ocr, extract_fields
from gpu_utils import check_gpu_usage
from database import init_db, save_result_to_db

# Load environment variables
load_dotenv()

# Initialize the database
init_db()  # <-- NEW line

# Create results directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULT_FOLDER = os.path.join(BASE_DIR, 'data', 'resultados')
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Add the project root to Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE

def callback(ch, method, properties, body):
    """
    Callback function that processes student ID card OCR jobs from the queue
    """
    try:
        # Parse the message
        data = json.loads(body)
        job_id = data.get('job_id')
        filename = data.get('filename')
        
        print(f"Processing student ID card job {job_id} with image {filename}")
        
        if not os.path.exists(filename):
            print(f"Error: Image file not found at {filename}")
            save_error_result(job_id, "Student ID card image file not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Perform OCR on the student ID card image
        ocr_result = process_image_ocr(filename)
        
        if ocr_result:
            # Extract structured data from OCR text
            result_data = extract_fields(ocr_result)
            
            # Add confidence scores for extracted fields
            result_data["confidence"] = {
                "nombre": 1.0 if result_data["nombre"] else 0.0,
                "codigo_estudiante": 1.0 if result_data["codigo_estudiante"] else 0.0,
                "carrera": 1.0 if result_data["carrera"] else 0.0
            }
            
            # Add metadata to the result
            result_data["job_id"] = job_id
            result_data["status"] = "completado"
            result_data["processed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Save result to file
            result_file = os.path.join(RESULT_FOLDER, f"{job_id}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            # Save result to database
            save_result_to_db(result_data)  # <-- NEW line
            
            print(f"Student ID card job {job_id} completed successfully")
        else:
            save_error_result(job_id, "Student ID card OCR processing failed")
            print(f"Job {job_id} failed - OCR processing error")
            
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing student ID card: {e}")
        try:
            if 'job_id' in locals():
                save_error_result(job_id, str(e))
        except:
            pass
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def save_error_result(job_id, error_message):
    """Helper function to save error results"""
    result_file = os.path.join(RESULT_FOLDER, f"{job_id}.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "job_id": job_id,
            "status": "error",
            "error": error_message,
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2, ensure_ascii=False)

def start_worker():
    """Main function to start the worker"""
    gpu_status = check_gpu_usage()
    if gpu_status["gpu_available"]:
        print(f"GPU available with {gpu_status['gpu_utilization']}% utilization")
        print(f"GPU memory: {gpu_status['memory_used_mb']}/{gpu_status['memory_total_mb']} MB")
    else:
        print("Warning: GPU not available, using CPU only")
        print(f"Reason: {gpu_status.get('error', 'Unknown')}")
    
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT
            ))
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
            
            print("Worker started. Waiting for messages...")
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Worker stopped.")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
