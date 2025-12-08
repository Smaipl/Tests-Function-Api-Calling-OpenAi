import hashlib
import json
import os
from typing import Any


class CacheManager:
    def __init__(self, cache_dir: str = "test_results/cache", enabled: bool = False):
        self.cache_dir = cache_dir
        self.enabled = enabled
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _make_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    import json

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = os.path.join(self.cache_dir, f"{self._make_key(key)}.json")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️ Кэш повреждён ({path}): {e}")
                return None
        return None

    def set(self, key: str, data: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = os.path.join(self.cache_dir, f"{self._make_key(key)}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except TypeError as e:
            print(f"⚠️ Ошибка сериализации при сохранении кэша: {e}")
