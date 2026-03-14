import os
import re


def substitute_placeholders(text: str) -> str:
    """
    Заменяет маркеры вида <#secret.KEY> на значения из переменных окружения.
    Если переменной нет, оставляет маркер как есть.
    """
    pattern = r"<#secret\.([A-Z0-9_]+)>"

    def replacer(match):
        key = match.group(1)
        return os.getenv(key, match.group(0))

    return re.sub(pattern, replacer, text)
