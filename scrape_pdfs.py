import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from datetime import datetime
import PyPDF2
import sqlite3

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
        
        # Инициализируем базу данных
        self.init_db()
    
    def init_db(self):
        """Инициализация SQLite базы данных для хранения информации о PDF файлах"""
        self.conn = sqlite3.connect('pdf_documents.db')
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extracted_title TEXT
            )
        ''')
        self.conn.commit()
    
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
        """Сохранение записи о документе в базу данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO documents (title, filename, url, extracted_title)
                VALUES (?, ?, ?, ?)
            ''', (title, filename, url, extracted_title))
            self.conn.commit()
            print(f"Запись для {filename} сохранена в базу данных")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
    
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
            
            # Скачиваем файл
            filepath = self.download_pdf(url, filename)
            if filepath:
                # Извлекаем заголовок из PDF
                extracted_title = self.extract_title_from_pdf(filepath)
                
                # Сохраняем запись в базу данных
                self.save_document_record(original_title, filename, url, extracted_title)
        
        print("Процесс завершен")


def main():
    scraper = PDFScraper()
    scraper.process_pdfs()


if __name__ == "__main__":
    main()