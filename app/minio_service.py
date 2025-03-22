import hashlib
from dotenv import load_dotenv
load_dotenv()
from io import BytesIO
import os
from app.minio_client import MinioClient


minio_client = MinioClient(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_USER"),
    secret_key=os.getenv("MINIO_PASSWORD"),
    bucket_name=os.getenv("MINIO_BUCKET"),
)


def upload_to_minio(content: bytes, filename: str) -> str:
    # Генерация sha256 хэша для файла
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Загружаем файл в MinIO
    file_stream = BytesIO(content)
    minio_client.client.put_object(
        minio_client.bucket_name,
        sha256_hash,  # Используем хэш как имя объекта
        file_stream,
        len(content),
    )
    return sha256_hash


def download_file(file_hash, local_path):
    """Скачивает файл из MinIO и сохраняет его локально."""
    minio_client.client.fget_object(minio_client.bucket_name, file_hash, local_path)


def check_file_exists(sha256_hash: str) -> bool:
    # Проверка, существует ли файл с таким хэшем в MinIO
    existing_files = minio_client.client.list_objects(
        minio_client.bucket_name, recursive=True
    )
    for file in existing_files:
        if file.object_name.endswith(sha256_hash):  # Проверка по хэшу в названии файла
            return True
    return False


def get_all_files():
    """Возвращает список всех файлов в MinIO (по их хэшам)."""
    return [
        obj.object_name
        for obj in minio_client.client.list_objects(
            minio_client.bucket_name, recursive=True
        )
    ]
