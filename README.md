OCR para Carnés Estudiantiles
Este proyecto implementa un sistema OCR (Reconocimiento Óptico de Caracteres) para extraer información de carnés estudiantiles utilizando modelos de visión en Ollama.
Siendo honesto el codigo es un monton de scripts pegados con cinta y de alguna forma funciona
📋 Descripción
El sistema procesa imágenes de carnés estudiantiles y extrae información estructurada como:

Nombre del estudiante
Código/ID del estudiante
Carrera/Programa
Institución educativa

Utiliza una API, una cola de mensajes RabbitMQ y un worker que procesa las imágenes usando el modelo *qwen2.5vl:7b* (de los 9 modelos probados fue el unico que dijo que si era capaz de usar CPU + GPU toda una maravilla)

🖥️ Requisitos del Sistema
Python 3.8+
NVIDIA GPU con al menos 6GB de VRAM (recomendado) (Si tienes menos el script explota (puedes hacer downgrade a llava:7b pero los resultados son muy malos))
Docker (opcional, para RabbitMQ)
Ollama 0.7.0+

🛠️ Instalación
1. Clonar el repositorio
git clone https://github.com/Pidual/PROYECTO-OCR.git
cd PROYECTO-OCR

2. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

3. Instalar Ollama (LINUX)
curl -fsSL https://ollama.com/install.sh | sh

4. Instalar RabbitMQ (mas comodo con docker en mi opinion)
docker run -d --name rabbitmq -p 5673:5672 -p 15673:15672 rabbitmq:management

5. Descargar un modelo de visión (💙qwen2.5vl:7b💙)
ollama pull qwen2.5vl:7b  

⚙️ Configuración
Crea un archivo .env en la raíz del proyecto:

🚀 Uso
Iniciar el sistema
O especificar un modelo directamente:

Enviar imágenes para procesamiento
Vía cURL:

Respuesta:

Verificar resultados
Respuesta:

🔍 Solución de problemas
Errores de GPU
Si la GPU no tiene memoria suficiente, prueba modelos más ligeros:

Y actualiza el modelo en el archivo .env.

Ollama no usa la GPU
Asegúrate de que Ollama esté configurado para usar la GPU:

Resultados de OCR incorrectos
Prueba diferentes modelos y ajusta el sistema en ocr_processor.py para mejorar el reconocimiento.

📊 Ejemplos
Ejemplo de integración con una aplicación web:

📝 Licencia
Este proyecto está bajo la licencia MIT.
