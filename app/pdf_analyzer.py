import json
import hashlib
import os
import re
from pdfminer.high_level import extract_text
from keybert import KeyBERT
import pymorphy3
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


class PDFAnalyzer:
    """Класс для анализа PDF-файлов в указанной папке и генерации метаданных."""
    
    def __init__(self, folder_path: str, output_json: str = "all_files_metadata.json"):
        self.folder_path = folder_path
        self.output_json = output_json
        self.kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        self.morph = pymorphy3.MorphAnalyzer()

    def compute_sha256(self, file_path: str) -> str:
        """Вычисляет SHA-256 хэш файла."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def extract_pdf_text(self, file_path: str) -> str:
        """Извлекает текст из PDF и очищает его."""
        text = extract_text(file_path)
        text = re.sub(r'\s+', ' ', text)  # Убираем лишние пробелы и переводы строк
        return text

    def lemmatize_word(self, word: str) -> str:
        """Лемматизация русского слова."""
        return self.morph.parse(word)[0].normal_form

    def generate_tags(self, text: str, top_n: int = 5) -> list[str]:
        """Генерирует теги с учетом лемматизации и фильтрации."""
        keywords = self.kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=top_n * 2)
        
        # Лемматизация и фильтрация тегов
        tags = set()
        for kw, _ in keywords:
            word = kw.lower().strip()
            if word not in ENGLISH_STOP_WORDS and len(word) > 2:
                if re.match(r'^[а-яА-ЯёЁ]+$', word):  # Проверяем, что слово русское
                    word = self.lemmatize_word(word)
                tags.add(word)

            if len(tags) >= top_n:
                break

        return list(tags)

    def analyze_folder(self) -> None:
        """Анализирует все PDF-файлы в папке и сохраняет метаданные в JSON."""
        metadata_list = []
        
        for file_name in os.listdir(self.folder_path):
            if file_name.lower().endswith(".pdf"):
                file_path = os.path.join(self.folder_path, file_name)
                text = self.extract_pdf_text(file_path)
                sha256_hash = self.compute_sha256(file_path)
                tags = self.generate_tags(text)
                
                metadata = {
                    "file_name": file_name,
                    "sha256": sha256_hash,
                    "tags": tags
                }
                metadata_list.append(metadata)
                print(f"Обработан: {file_name}")

        with open(self.output_json, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=4)

        print(f"Все метаданные сохранены в {self.output_json}")
        

if __name__ == "__main__":
    folder_path = "data"  # Укажите путь к папке с PDF
    analyzer = PDFAnalyzer(folder_path)
    analyzer.analyze_folder()
