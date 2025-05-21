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
            loadingDiv.style.display = 'none';
            displayResults(data);

        } catch (error) {
            loadingDiv.style.display = 'none';
            resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    });

    function displayResults(data) {
        let htmlContent = '<div class="results-container">';
        htmlContent += '<h2>Resultados del Análisis</h2>';

        if (data.texto_detectado) {
            htmlContent += `<div class="result-section">
                <h3>Texto Detectado:</h3>
                <p>${data.texto_detectado}</p>
            </div>`;
        }

        if (data.datos_extraidos) {
            htmlContent += `<div class="result-section">
                <h3>Datos Extraídos:</h3>
                <pre>${JSON.stringify(data.datos_extraidos, null, 2)}</pre>
            </div>`;
        }

        htmlContent += '</div>';
        resultDiv.innerHTML = htmlContent;
    }
});
