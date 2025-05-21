document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');
    const imagePreview = document.getElementById('imagePreview');
    const imageInput = document.getElementById('imageInput');

    // Previsualización de la imagen
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData();
        const imageFile = imageInput.files[0];

        if (!imageFile) {
            alert('Por favor selecciona una imagen');
            return;
        }

        formData.append('image', imageFile);

        // Mostrar barra de carga
        loadingDiv.style.display = 'block';
        resultDiv.innerHTML = '';

        try {
            const response = await fetch('/procesar-imagen', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Error en el procesamiento de la imagen');
            }

            const data = await response.json();
            if (data.job_id) {
                checkProcessingStatus(data.job_id);
            } else {
                throw new Error("ID de trabajo no recibido del servidor");
            }
        } catch (error) {
            loadingDiv.style.display = "none";
            resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    });

    async function checkProcessingStatus(jobId) {
        async function checkStatus() {
            try {
                const response = await fetch(`/resultado/${jobId}`);
                const result = await response.json();

                if (result.status === "procesando") {
                    loadingDiv.innerHTML = `
                        <div class="spinner"></div>
                        <p>Procesando imagen, por favor espere...</p>
                        <p><small>ID de proceso: ${jobId}</small></p>
                        <p><small>Si tienes GPU, el procesamiento será más rápido.</small></p>
                    `;
                    setTimeout(checkStatus, 2000);
                } else if (result.status === "error" || result.error) {
                    loadingDiv.style.display = "none";
                    resultDiv.innerHTML = `<p class="error">Error: ${result.error || "Ocurrió un error en el procesamiento."}</p>`;
                } else {
                    loadingDiv.style.display = "none";
                    displayResults(result);
                }
            } catch (error) {
                loadingDiv.style.display = "none";
                resultDiv.innerHTML = `<p class="error">Error consultando resultados: ${error.message}</p>`;
            }
        }
        checkStatus();
    }

    function displayResults(data) {
        let htmlContent = '<div class="results-container">';
        htmlContent += '<h2>Resultados del Análisis</h2>';

        if (data.raw_text) {
            htmlContent += `<div class="result-section">
                <h3>Texto Detectado:</h3>
                <p>${data.raw_text}</p>
            </div>`;
        } else if (data.texto_detectado) {
            htmlContent += `<div class="result-section">
                <h3>Texto Detectado:</h3>
                <p>${data.texto_detectado}</p>
            </div>`;
        }

        htmlContent += `<div class="result-section">
            <h3>Datos Extraídos:</h3>
            <div class="data-grid">`;

        if (data.nombre) {
            htmlContent += `<div class="data-item">
                <label>Nombre:</label>
                <span>${data.nombre}</span>
            </div>`;
        }

        if (data.codigo_estudiante) {
            htmlContent += `<div class="data-item">
                <label>Código:</label>
                <span>${data.codigo_estudiante}</span>
            </div>`;
        }

        if (data.carrera) {
            htmlContent += `<div class="data-item">
                <label>Carrera:</label>
                <span>${data.carrera}</span>
            </div>`;
        }

        if (data.institucion) {
            htmlContent += `<div class="data-item">
                <label>Institución:</label>
                <span>${data.institucion}</span>
            </div>`;
        }

        htmlContent += `</div></div>`;
        htmlContent += '</div>';
        resultDiv.innerHTML = htmlContent;
    }
});