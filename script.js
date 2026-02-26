document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const outputElement = document.getElementById('output');
    
    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        
        if (!file) {
            return;
        }
        
        // Проверяем, что файл имеет расширение .docx
        if (!file.name.endsWith('.docx')) {
            outputElement.innerHTML = '<p class="error">Пожалуйста, выберите файл в формате DOCX</p>';
            return;
        }
        
        // Создаем FileReader для чтения содержимого файла
        const reader = new FileReader();
        
        reader.onload = function(loadEvent) {
            const arrayBuffer = loadEvent.target.result;
            
            // Используем mammoth.js для конвертации DOCX в HTML
            mammoth.convertToHtml({arrayBuffer: arrayBuffer})
                .then(function(result) {
                    // Вставляем результат в элемент вывода
                    outputElement.innerHTML = result.value;
                    
                    // Отображаем предупреждения, если есть
                    const messages = result.messages;
                    if (messages.length > 0) {
                        console.log("Предупреждения при обработке файла:", messages);
                    }
                })
                .catch(function(error) {
                    outputElement.innerHTML = '<p class="error">Ошибка при обработке файла: ' + error.message + '</p>';
                    console.error("Ошибка при обработке DOCX файла:", error);
                });
        };
        
        reader.onerror = function() {
            outputElement.innerHTML = '<p class="error">Ошибка при чтении файла</p>';
        };
        
        // Читаем файл как ArrayBuffer
        reader.readAsArrayBuffer(file);
    });
});