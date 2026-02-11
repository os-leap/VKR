import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from datetime import datetime
import PyPDF2
import json

class PDFScraper:
    def __init__(self, base_url="https://edsoo.ru/normativnye-dokumenty/", download_dir="./pdf_downloads"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Создаем директорию для скачивания если не существует
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Инициализируем JSON файл для хранения информации о PDF файлах
        self.json_file = 'knowledge_base.json'
        self.load_documents()
    
    def load_documents(self):
        """Загрузка документов из JSON файла"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            else:
                self.documents = []
        except Exception as e:
            print(f"Ошибка при загрузке документов из JSON: {e}")
            self.documents = []
    
    def check_existing_document(self, filename):
        """Проверка существования документа в JSON файле"""
        for doc in self.documents:
            if doc.get('filename') == filename:
                # Проверяем, является ли документ связанным с ФГОС
                if 'фгос' in doc.get('title', '').lower() or 'фгт' in doc.get('title', '').lower():
                    # Обновляем название документа с текущей датой
                    current_date = datetime.now().strftime('%d.%m.%Y')
                    doc['title'] = f"Обновление ФГОС_{current_date}"
                    # Обновляем запись в JSON файле
                    self.save_document_record(doc['title'], doc['filename'], doc['url'], doc.get('extracted_title'))
                    print(f"Обновлено название для ФГОС документа {filename}")
                return doc
        return None
    
    def get_all_documents(self):
        """Получение всех документов из JSON файла"""
        return self.documents
    
    def get_status(self):
        """Получение статуса обработки"""
        return {
            'total_documents': len(self.documents),
            'last_update': max([doc.get('download_date') for doc in self.documents], default=None) if self.documents else None
        }
    
    def get_page_content(self):
        """Получение содержимого страницы"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при получении страницы: {e}")
            return None

    def extract_pdf_links(self, html_content):
        """Извлечение ссылок на PDF файлы"""
        soup = BeautifulSoup(html_content, 'html.parser')
        pdf_links = []
        
        # Поиск всех ссылок, ведущих к PDF файлам
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                # Преобразование относительных ссылок в абсолютные
                full_url = urllib.parse.urljoin(self.base_url, href)
                title = link.get_text(strip=True) or link.find_previous_sibling(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if hasattr(title, 'get_text'):
                    title = title.get_text(strip=True)
                elif not title:
                    title = os.path.basename(href)
                
                # Проверяем, содержит ли название документа что-то связанное с ФГОС
                if 'фгос' in title.lower() or 'фгт' in title.lower() or 'федеральные государственные образовательные стандарты' in title.lower():
                    # Формируем специальное название с датой
                    current_date = datetime.now().strftime('%d.%m.%Y')
                    title = f"Обновление ФГОС_{current_date}"
                
                pdf_links.append({
                    'url': full_url,
                    'title': title
                })
        
        return pdf_links
    def download_pdf(self, url, filename):
        """Скачивание PDF файла"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Файл {filename} успешно скачан")
            return filepath
        except requests.RequestException as e:
            print(f"Ошибка при скачивании {url}: {e}")
            return None
    
    def extract_title_from_pdf(self, filepath):
        """Извлечение заголовка из PDF файла"""
        try:
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                if len(pdf_reader.pages) > 0:
                    page = pdf_reader.pages[0]
                    text = page.extract_text()
                    
                    # Простое извлечение заголовка - первые несколько строк текста
                    lines = text.split('\n')
                    title_lines = []
                    for line in lines[:10]:  # Проверяем первые 10 строк
                        clean_line = line.strip()
                        if clean_line and len(clean_line) > 10:  # Пропускаем короткие строки
                            title_lines.append(clean_line)
                            if len(title_lines) >= 3:  # Берем первые 3 значимые строки
                                break
                    
                    return ' '.join(title_lines) if title_lines else "Заголовок не найден"
        except Exception as e:
            print(f"Ошибка при извлечении заголовка из {filepath}: {e}")
            return "Ошибка извлечения заголовка"
    
    def save_document_record(self, title, filename, url, extracted_title=None):
        """Сохранение записи о документе в JSON файл"""
        # Проверяем, существует ли уже запись с таким же filename
        existing_doc_index = None
        for i, doc in enumerate(self.documents):
            if doc.get('filename') == filename:
                existing_doc_index = i
                break
        
        # Создаем новую запись
        document_record = {
            'id': len(self.documents) + 1 if existing_doc_index is None else self.documents[existing_doc_index]['id'],
            'title': title,
            'filename': filename,
            'url': url,
            'download_date': datetime.now().isoformat(),
            'extracted_title': extracted_title
        }
        
        # Если запись существует, обновляем её, иначе добавляем новую
        if existing_doc_index is not None:
            self.documents[existing_doc_index] = document_record
        else:
            # Назначаем новый ID, если это новая запись
            max_id = max([doc.get('id', 0) for doc in self.documents], default=0)
            document_record['id'] = max_id + 1
            self.documents.append(document_record)
        
        # Сохраняем обновленный список в JSON файл
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            print(f"Запись для {filename} сохранена в JSON файл")
        except Exception as e:
            print(f"Ошибка при сохранении в JSON файл: {e}")

    def process_pdfs(self):
        """Основной метод для обработки PDF файлов"""
        print("Начинаю процесс парсинга и скачивания PDF файлов...")
        
        html_content = self.get_page_content()
        if not html_content:
            print("Не удалось получить содержимое страницы")
            return
        
        pdf_links = self.extract_pdf_links(html_content)
        print(f"Найдено {len(pdf_links)} PDF файлов")
        
        for link_info in pdf_links:
            url = link_info['url']
            original_title = link_info['title']
            
            # Получаем имя файла из URL
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            if not filename:
                filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Проверяем, существует ли уже такой файл
            existing_doc = self.check_existing_document(filename)
            if existing_doc:
                print(f"Файл {filename} уже существует в базе данных, пропускаем")
                continue
            
            # Скачиваем файл
            filepath = self.download_pdf(url, filename)
            if filepath:
                # Извлекаем заголовок из PDF
                extracted_title = self.extract_title_from_pdf(filepath)
                
                # Сохраняем запись в JSON файл
                self.save_document_record(original_title, filename, url, extracted_title)
    
