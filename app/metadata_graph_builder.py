import json
from collections import defaultdict
from typing import Dict
import structlog

logger = structlog.get_logger()

class MetadataGraphBuilder:
    """Класс для построения графа на основе метаданных файлов."""

    def __init__(self, input_json: str, output_json: str = "graph_data.json"):
        """
        Инициализация класса.

        :param input_json: Путь к входному JSON с метаданными файлов.
        :param output_json: Путь для сохранения выходного JSON с графом.
        """
        self.input_json = input_json
        self.output_json = output_json

    def load_metadata(self) -> Dict[str, Dict]:
        """Загружает метаданные из JSON-файла."""
        try:
            with open(self.input_json, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            if not isinstance(metadata, dict):
                raise ValueError("Неверный формат метаданных, ожидается словарь")
            logger.info("Метаданные успешно загружены", file_count=len(metadata))
            return metadata
        except Exception as e:
            logger.error("Ошибка загрузки метаданных", error=str(e))
            return {}

    def build_graph(self) -> Dict:
        """Создаёт граф на основе файлов и их тегов."""
        logger.info("Начало построения графа")

        metadata = self.load_metadata()
        if not metadata:
            logger.warning("Метаданные пусты, граф не будет построен")
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        tag_to_files = defaultdict(list)

        # Добавляем файлы как узлы
        for file_hash, file_data in metadata.items():
            try:
                file_name = file_data["filename"]
                tags = file_data.get("tags", [])

                nodes.append({"id": file_hash, "label": file_name, "type": "file", "tags": tags})
                logger.info("Добавлен узел", file_hash=file_hash, file_name=file_name, tags=tags)

                for tag in tags:
                    tag_to_files[tag].append(file_hash)
            except KeyError as e:
                logger.error("Ошибка в структуре данных файла", error=str(e), file_hash=file_hash, file_data=file_data)

        # Связываем файлы между собой по общим тегам
        for tag, file_ids in tag_to_files.items():
            for i in range(len(file_ids)):
                for j in range(i + 1, len(file_ids)):
                    edges.append({"source": file_ids[i], "target": file_ids[j], "type": "related_by_tag"})
            logger.info("Добавлены связи по тегу", tag=tag, file_ids=file_ids)

        logger.info("Граф успешно построен", node_count=len(nodes), edge_count=len(edges))
        return {"nodes": nodes, "edges": edges}

    def save_graph(self) -> None:
        """Сохраняет граф в JSON-файл."""
        graph_data = self.build_graph()
        if not graph_data["nodes"]:
            logger.warning("Граф пуст, файл не будет записан")
            return

        try:
            with open(self.output_json, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=4)
            logger.info("Граф успешно сохранён", output_file=self.output_json)
        except Exception as e:
            logger.error("Ошибка сохранения графа", error=str(e))

if __name__ == "__main__":
    input_metadata_json = "all_files_metadata.json"
    graph_builder = MetadataGraphBuilder(input_metadata_json)
    graph_builder.save_graph()
