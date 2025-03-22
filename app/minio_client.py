from minio import Minio
from minio.error import S3Error
import os

class MinioClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str):
        """
        Инициализация клиента MinIO.

        :param endpoint: Адрес MinIO (например, 'localhost:9000').
        :param access_key: Ключ доступа.
        :param secret_key: Секретный ключ.
        :param bucket_name: Название бакета.
        """
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self.bucket_name = bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Проверяет наличие бакета и создаёт его, если он не существует."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Ошибка при проверке/создании бакета: {e}")

    def upload_file(self, file_path: str, object_name: str) -> None:
        """Загружает файл в MinIO."""
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
            print(f"Файл {file_path} загружен как {object_name}.")
        except S3Error as e:
            print(f"Ошибка при загрузке файла: {e}")

    def upload_file_from_bytes(self, file_data: bytes, object_name: str) -> None:
        """Загружает файл в MinIO из байтов."""
        from io import BytesIO
        try:
            file_stream = BytesIO(file_data)
            self.client.put_object(self.bucket_name, object_name, file_stream, len(file_data))
            print(f"Файл загружен как {object_name}.")
        except S3Error as e:
            print(f"Ошибка при загрузке файла из байтов: {e}")
