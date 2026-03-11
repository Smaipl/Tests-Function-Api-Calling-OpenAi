import json
from typing import Any


class BaseFunctionException(Exception):
    def __init__(self, message: str = "", fields: Any = None):
        self.message = message
        self.fields = (
            fields if isinstance(fields, (list, dict, str, int)) else str(fields)
        )
        super().__init__(self.message)

    def __str__(self):
        try:
            details = json.dumps(self.fields, indent=4, ensure_ascii=False)
        except (TypeError, ValueError):
            details = repr(self.fields)

        return f"\n❌ {self.message}\nДетали: {details}"


class EmptyRequiredFields(BaseFunctionException):
    """Ошибка: в JSON-схеме отсутствуют обязательные поля для работы функции."""

    pass


class TypeMismatchJsonToPython(BaseFunctionException):
    """Ошибка: несоответствие типов данных между JSON-схемой и Python-кодом."""

    pass


class UnregisterField(BaseFunctionException):
    """Ошибка: в коде используется аргумент, не зарегистрированный в JSON-схеме."""

    pass


class FunctionNameMismatch(BaseFunctionException):
    """Ошибка: имя функции в коде не совпадает с именем в JSON-схеме."""

    pass


class InvalidFunctionSignature(BaseFunctionException):
    """Ошибка: функция принимает не те аргументы (должен быть только 'arguments')."""

    pass


class SchemaSyncError(BaseFunctionException):
    """Ошибка: рассинхрон между аргументами в коде (.get) и JSON-схемой."""

    pass


class DefaultValueMismatch(BaseFunctionException):
    """Ошибка: значение по умолчанию в коде не совпадает с дефолтом в схеме."""

    pass
