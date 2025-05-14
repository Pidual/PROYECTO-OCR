import os
import json
import pika
import time
import sys

# Add the src directory to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.shared.ocr import perform_ocr

# Create results directory with updated path
RESULT_FOLDER = 'data/resultados'
os.makedirs(RESULT_FOLDER, exist_ok=True)

def extract_fields(ocr_text):
    """
    Extract relevant fields from OCR text.
    This is a simple implementation - you might need to enhance this
    based on your specific document structure.
    """
    fields = {
        "raw_text": ocr_text,
        "nombre": "",
        "codigo": "",
        "carrera": ""
    }
    
    # Simple field extraction logic - improve based on your document format
    lines = ocr_text.split('\n')
    for line in lines:
        if "Nombre:" in line:
            fields["nombre"] = line.replace("Nombre:", "").strip()
        elif "Código:" in line:
            fields["codigo"] = line.replace("Código:", "").strip()
        elif "Carrera:" in line:
            fields["carrera"] = line.replace("Carrera:", "").strip()
    
    return fields

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        job_id = data.get('job_id')
        filename = data.get('filename')
        
        print(f"Processing job {job_id} with image {filename}")
        
        # Perform OCR on the image
        ocr_result = perform_ocr(filename)
        
        if ocr_result:
            # Extract structured data from OCR text
            result_data = extract_fields(ocr_result)
            
            # Add status to the result
            result_data["job_id"] = job_id
            result_data["status"] = "completado"
            
            # Save result to file
            result_file = f"{RESULT_FOLDER}/{job_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
                
            print(f"Job {job_id} completed successfully")
        else:
            # Save error result
            result_file = f"{RESULT_FOLDER}/{job_id}.json"
            with open(result_file, 'w') as f:
                json.dump({
                    "job_id": job_id,
                    "status": "error",
                    "error": "Failed to process image"
                }, f, indent=2)
            
            print(f"Job {job_id} failed")
            
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Negative acknowledgment in case of failure
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_worker():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='ocr_queue', durable=True)
        
        # Set prefetch count to 1 to distribute load evenly among workers
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='ocr_queue', on_message_callback=callback)
        
        print("Worker started. Waiting for messages...")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.")
    except Exception as e:
        print(f"Worker error: {e}")
        time.sleep(5)  # Wait before reconnecting
        start_worker()  # Recursive retry

if __name__ == "__main__":
    start_worker()