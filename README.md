
---

# 🧠 OCR para Carnés Estudiantiles

Este proyecto implementa un sistema de Reconocimiento Óptico de Caracteres (OCR) para extraer información estructurada de carnés estudiantiles, utilizando modelos de visión integrados con [Ollama](https://ollama.com/).

> ⚠️ *Honestamente, el código es una colección de scripts pegados con cinta... pero funciona. Milagrosamente.*

---

## 📋 Descripción

El sistema procesa imágenes de carnés estudiantiles y extrae información como:

* 🧑‍🎓 Nombre del estudiante
* 🆔 Código o ID del estudiante
* 🧭 Carrera o programa
* 🏛️ Institución educativa

Está compuesto por:

* Una API
* Una cola de mensajes (RabbitMQ)
* Un worker que utiliza el modelo `qwen2.5vl:7b` para procesar las imágenes

> 🎯 *De los 9 modelos probados, `qwen2.5vl:7b` fue el único que dijo “sí” a CPU + GPU. Toda una joya.*

---

## 🖥️ Requisitos del Sistema

* Python `3.8+`
* NVIDIA GPU con al menos `6GB VRAM` (⚠️ Si tienes menos, el script explotará)
* Docker (opcional, recomendado para RabbitMQ)
* Ollama `0.7.0+`

> 💡 Si necesitas usar un modelo más liviano, puedes hacer downgrade a `llava:7b`, pero los resultados son bastante pobres.

---

## 🛠️ Instalación

1. **Clonar el repositorio:**

```bash
git clone https://github.com/Pidual/PROYECTO-OCR.git
cd PROYECTO-OCR
```

2. **Crear entorno virtual e instalar dependencias:**

```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Instalar Ollama (Linux):**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

4. **Instalar RabbitMQ (usando Docker):**

```bash
docker run -d --name rabbitmq -p 5673:5672 -p 15673:15672 rabbitmq:management
```

5. **Descargar modelo de visión recomendado:**

```bash
ollama pull qwen2.5vl:7b
```

---

## ⚙️ Configuración

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# Configuración básica
DEBUG=True
PORT=5000
HOST=0.0.0.0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5673
RABBITMQ_QUEUE=ocr_queue

# Ollama
OLLAMA_API_URL=http://localhost:11434/api
```

> 🔒 La variable `OLLAMA_MODEL` está *hardcoded* en la línea 11 de `ocr_processor.py`.

---

## 🚀 Uso

Iniciar el sistema (usando modelo por defecto) (chmod para que sea executable):

```bash
chmod +x run.py
./run.py --all --monitor
```

> También puedes especificar el modelo directamente.
> SI todo esta funcionando deberias ver esto en el terminal
**![image](https://github.com/user-attachments/assets/2e60a33e-f158-482d-aad4-6533ddd887f8)
**
---

## 🖼️ Enviar imágenes para procesamiento

Ejemplo de uso visual:

![image](https://github.com/user-attachments/assets/ce528db0-6365-41f3-87e5-3deb6432f974)

Resultado esperado:
![image](https://github.com/user-attachments/assets/031e2d7f-a391-4087-9ebd-ed91dcc277a9)

---

## 🔍 Solución de problemas

**Errores de GPU:**

* Si tu GPU no tiene suficiente VRAM, cambia a un modelo más liviano (aunque los resultados serán meh 😞).
* No olvides actualizar el modelo en el `.env`.
* este comando es util para revisar nvidia-smi ollama ps y los procesos de python todo al mismo tiempo en la misma terminal (me sirvio arto para revisar que el modelo usara la GPU corectamente ademas informacion interesante como cuanta luz se esta jalando el modelo xD) `watch -n 1 "nvidia-smi && echo '' && ollama ps && echo '' && ps aux | grep python | grep -v grep"`


---

WHAWHWAHWAH HAWHWAH AWHWAHAW HWAHWAH HAWH WHA HAH AWWHWHA HWA A Todo este codigo fue generado en un 98% por claude SOnnet3.7 :) 
![6d8](https://github.com/user-attachments/assets/f3baff38-f024-46b7-a9f3-2763bd825f1f)
