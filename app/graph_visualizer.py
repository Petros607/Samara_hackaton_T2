import json
from pyvis.network import Network
from typing import Dict

class GraphVisualizer:
    def __init__(self, data: Dict, output_file: str = "graph.html"):
        self.data = data
        self.output_file = output_file
        self.net = Network(
            notebook=False, height="800px", width="100%", bgcolor="#222222", font_color="white"
        )
        # Настройки физики
        self.net.force_atlas_2based(
            gravity=-100,  # Уменьшает притяжение узлов
            central_gravity=0.01,  # Делает центр слабее
            spring_length=200,  # Увеличивает длину рёбер
            spring_strength=0.03,  # Ослабляет связь рёбер
        )

    def add_nodes(self) -> None:
        for node in self.data["nodes"]:
            title = f"{node['label']}<br>{node.get('tags', 'Нет информации')}"
            self.net.add_node(node["id"], label=node["label"], title=title, color="blue")

    def add_edges(self) -> None:
        for edge in self.data["edges"]:
            self.net.add_edge(edge["source"], edge["target"], color="gray", length=300)  # Длинные связи

    def build_graph(self) -> None:
        self.add_nodes()
        self.add_edges()
        self.net.toggle_physics(True)
        self.net.show(self.output_file, notebook=False)
        print(f"Граф сохранён в {self.output_file}")

    @staticmethod
    def load_graph_data(file_path: str) -> Dict:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

if __name__ == "__main__":
    graph_data = GraphVisualizer.load_graph_data("graph_data.json")
    visualizer = GraphVisualizer(graph_data)
    visualizer.build_graph()
