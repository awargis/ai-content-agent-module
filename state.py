import json
from pathlib import Path


class StateStore:
    def __init__(self, path: str, max_items: int = 5000):
        self.path = Path(path)
        self.max_items = max_items
        self.data = {"processed_ids": [], "processed_hashes": []}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            self.data["processed_ids"] = loaded.get("processed_ids", [])
            self.data["processed_hashes"] = loaded.get("processed_hashes", [])
        except (json.JSONDecodeError, OSError):
            # A corrupt state file should not crash collection.
            self.data = {"processed_ids": [], "processed_hashes": []}

    def has_id(self, value: str) -> bool:
        return value in self.data["processed_ids"]

    def has_hash(self, value: str) -> bool:
        return value in self.data["processed_hashes"]

    def add(self, article_id: str, content_hash: str) -> None:
        self.data["processed_ids"].append(article_id)
        self.data["processed_hashes"].append(content_hash)
        self.data["processed_ids"] = list(dict.fromkeys(self.data["processed_ids"]))[-self.max_items:]
        self.data["processed_hashes"] = list(dict.fromkeys(self.data["processed_hashes"]))[-self.max_items:]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self.path)
