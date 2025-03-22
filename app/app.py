from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List, Union
import structlog
import os
from dotenv import load_dotenv
import hashlib

# Загрузка переменных окружения
load_dotenv()

# Импорт сервисов
from app.minio_service import upload_to_minio, check_file_exists, get_all_files, download_file
from app.metadata_service import load_metadata, save_metadata
from app.pdf_analyzer import PDFAnalyzer
from app.metadata_graph_builder import MetadataGraphBuilder
from app.graph_visualizer import GraphVisualizer

# Настройка логирования
logger = structlog.get_logger()

# Константы
TEMP_FOLDER = "temp_pdfs"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Инициализация FastAPI
app = FastAPI()

@app.post("/upload")
async def upload_files(files: Union[List[UploadFile], UploadFile] = File(...)):
    """Загрузка файлов в MinIO."""
    try:
        files = [files] if isinstance(files, UploadFile) else files
        uploaded_files = []
        metadata = load_metadata()

        for file in files:
            content = await file.read()
            sha256_hash = hashlib.sha256(content).hexdigest()
            if check_file_exists(sha256_hash):
                logger.info(f"Файл {file.filename} уже существует в MinIO.")
                uploaded_files.append({"filename": file.filename, "message": "Файл уже существует"})
            else:
                sha256_hash = upload_to_minio(content, file.filename)
                metadata[sha256_hash] = {"filename": file.filename}
                save_metadata(metadata)
                logger.info(f"Файл {file.filename} загружен в MinIO с хэшем {sha256_hash}.")
                uploaded_files.append({"filename": file.filename, "object_name": sha256_hash})

        return {"uploaded_files": uploaded_files}
    except Exception as e:
        logger.error(f"Ошибка при загрузке файлов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-and-visualize")
async def analyze_and_visualize():
    """Анализ PDF-файлов, генерация тегов и построение графа."""
    logger.info("Запуск анализа и построения графа")
    try:
        metadata = load_metadata()
        logger.info("Метаданные загружены", metadata=metadata)
        
        all_files = get_all_files()
        logger.info("Получен список всех файлов", file_count=len(all_files))
        
        analyzer = PDFAnalyzer(TEMP_FOLDER)
        updated = False

        for file_hash in all_files:
            if "tags" in metadata.get(file_hash, {}):
                logger.info("Пропускаем файл, теги уже существуют", file_hash=file_hash)
                continue
            
            file_path = os.path.join(TEMP_FOLDER, file_hash)
            logger.info("Скачиваем файл", file_hash=file_hash, file_path=file_path)
            download_file(file_hash, file_path)

            text = analyzer.extract_pdf_text(file_path)
            logger.info("Извлечён текст из PDF", file_hash=file_hash, text_length=len(text))
            
            tags = analyzer.generate_tags(text)
            logger.info("Сгенерированы теги", file_hash=file_hash, tags=tags)
            
            if tags:
                metadata.setdefault(file_hash, {}).update({"tags": tags})
                updated = True
            
            os.remove(file_path)
            logger.info("Удалён временный файл", file_path=file_path)

        if updated:
            save_metadata(metadata)
            logger.info("Метаданные обновлены")
        
        graph_builder = MetadataGraphBuilder("metadata.json")
        logger.info("Создание графа на основе метаданных")
        
        graph_data = graph_builder.build_graph()
        graph = GraphVisualizer(graph_data)
        graph.build_graph()
        
        logger.info("Граф успешно построен и сохранён как HTML")
        return FileResponse("graph.html", media_type="text/html")
    except Exception as e:
        logger.error("Ошибка при анализе и построении графа", error=e)
        raise HTTPException(status_code=500, detail=str(e))