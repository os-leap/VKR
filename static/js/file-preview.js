// File preview functionality
function showFilePreview(filename, filetype, filepath) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'file-preview-modal';
    modal.innerHTML = `
        <div class="file-preview-content">
            <div class="file-preview-header">
                <h3>Просмотр файла: ${filename}</h3>
                <button class="close-preview">&times;</button>
            </div>
            <div class="file-preview-body">
                ${getFilePreviewElement(filename, filetype, filepath)}
            </div>
            <div class="file-preview-footer">
                <button class="btn-download" onclick="downloadFile('${filepath}', '${filename}')">Скачать</button>
                <button class="btn-close-preview">Закрыть</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking close buttons
    modal.querySelector('.close-preview').addEventListener('click', closeModal);
    modal.querySelector('.btn-close-preview').addEventListener('click', closeModal);
    
    // Close modal when clicking outside the content
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

function getFilePreviewElement(filename, filetype, filepath) {
    const extension = filename.split('.').pop().toLowerCase();
    
    // For supported image formats
    if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(extension)) {
        return `<img src="${filepath}" alt="${filename}" style="max-width: 100%; max-height: 70vh;">`;
    }
    
    // For PDF files, try to use PDF.js if available or show a preview
    if (extension === 'pdf') {
        return `
            <iframe src="${filepath}" 
                    width="100%" 
                    height="600px" 
                    type="application/pdf"
                    style="border: none;">
                <p>Ваш браузер не поддерживает просмотр PDF. <a href="${filepath}" target="_blank">Нажмите здесь для скачивания</a>.</p>
            </iframe>
        `;
    }
    
    // For text-based documents, try to show content preview
    if (['txt', 'md', 'csv'].includes(extension)) {
        // For these files we'll just show a download button since we can't preview server-side content easily
        return `
            <div class="file-info">
                <p><strong>Тип файла:</strong> ${filetype || extension.toUpperCase()}</p>
                <p><strong>Размер:</strong> Загрузка...</p>
                <p>Файл текстового формата. Для просмотра содержимого рекомендуется скачать.</p>
            </div>
        `;
    }
    
    // For Office documents, show info and download link
    if (['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(extension)) {
        return `
            <div class="file-info">
                <p><strong>Тип файла:</strong> ${filetype || extension.toUpperCase()}</p>
                <p><strong>Расширение:</strong> ${extension}</p>
                <p>Документ Microsoft Office. Для просмотра содержимого рекомендуется скачать.</p>
            </div>
        `;
    }
    
    // For video formats, show video player
    if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(extension)) {
        return `
            <video controls width="100%" style="max-height: 70vh;">
                <source src="${filepath}" type="video/${extension}">
                Ваш браузер не поддерживает видео тег.
            </video>
        `;
    }
    
    // For unsupported formats, just show download button
    return `
        <div class="file-info">
            <p><strong>Тип файла:</strong> ${filetype || extension.toUpperCase()}</p>
            <p><strong>Расширение:</strong> ${extension}</p>
            <p>Формат файла не поддерживается для предварительного просмотра. Рекомендуется скачать файл.</p>
        </div>
    `;
}

function downloadFile(filepath, filename) {
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = filepath;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function closeModal() {
    const modal = document.querySelector('.file-preview-modal');
    if (modal) {
        document.body.removeChild(modal);
    }
}

// Initialize file preview functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for all file links
    const fileLinks = document.querySelectorAll('a[data-file-preview]');
    fileLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const filename = this.getAttribute('data-filename') || this.textContent.trim();
            const filepath = this.getAttribute('href');
            const filetype = this.getAttribute('data-filetype') || '';
            
            showFilePreview(filename, filetype, filepath);
        });
    });
});