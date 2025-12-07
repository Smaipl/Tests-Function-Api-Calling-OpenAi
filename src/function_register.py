"""
Универсальный реестр для регистрации и управления функциями.
Поддерживает любые функции с сигнатурой: func(arguments: Dict) -> str
"""
import importlib
import inspect
from typing import Dict, Any, List, Callable, Optional, Type
from dataclasses import dataclass
import json


@dataclass
class FunctionInfo:
	"""Информация о функции"""
	name: str
	func: Callable[[Dict[str, Any]], str]
	schema: Dict[str, Any]
	description: str = ""
	module: str = ""


class FunctionRegister:
	"""Универсальный реестр функций"""

	def __init__(self):
		self._functions: Dict[str, FunctionInfo] = {}
		self._schemas: Dict[str, Dict[str, Any]] = {}

	def register_function(
			self,
			function: Callable[[Dict[str, Any]], str],
			schema: Dict[str, Any],
			name: Optional[str] = None,
			description: Optional[str] = None
	) -> str:
		"""
		Регистрирует функцию в реестре.

		Args:
			function: Функция с сигнатурой Dict -> str
			schema: JSON-схема функции для OpenAI
			name: Имя функции (если None - берется из function.__name__)
			description: Описание функции

		Returns:
			Имя зарегистрированной функции
		"""
		func_name = name or function.__name__

		# Валидация сигнатуры
		self._validate_function_signature(function)

		# Валидация схемы
		self._validate_schema(schema, func_name)

		# Сохраняем информацию о функции
		self._functions[func_name] = FunctionInfo(
			name=func_name,
			func=function,
			schema=schema,
			description=description or schema.get("description", ""),
			module=function.__module__
		)

		self._schemas[func_name] = schema

		return func_name

	def register_from_module(self, module_name: str) -> List[str]:
		"""
		Регистрирует все функции из модуля.
		Ожидает, что модуль имеет словарь SCHEMAS с JSON-схемами.
		"""
		try:
			module = importlib.import_module(module_name)
		except ImportError as e:
			raise ValueError(f"Не удалось импортировать модуль {module_name}: {e}")

		registered = []

		# Ищем словарь SCHEMAS в модуле
		if not hasattr(module, "SCHEMAS"):
			raise ValueError(f"Модуль {module_name} не содержит словарь SCHEMAS")

		schemas = getattr(module, "SCHEMAS")

		# Регистрируем все функции, упомянутые в схемах
		for func_name, schema in schemas.items():
			if hasattr(module, func_name):
				func = getattr(module, func_name)
				if callable(func):
					self.register_function(func, schema, func_name)
					registered.append(func_name)

		return registered

	def get_function(self, name: str) -> Callable[[Dict[str, Any]], str]:
		"""Возвращает функцию по имени"""
		if name not in self._functions:
			raise KeyError(f"Функция '{name}' не найдена в реестре")
		return self._functions[name].func

	def get_schema(self, name: str) -> Dict[str, Any]:
		"""Возвращает JSON-схему функции"""
		if name not in self._schemas:
			raise KeyError(f"Схема для функции '{name}' не найдена")
		return self._schemas[name].copy()

	def get_all_schemas(self) -> List[Dict[str, Any]]:
		"""Возвращает все JSON-схемы"""
		return list(self._schemas.values())

	def get_function_info(self, name: str) -> FunctionInfo:
		"""Возвращает полную информацию о функции"""
		if name not in self._functions:
			raise KeyError(f"Функция '{name}' не найдена")
		return self._functions[name]

	def list_functions(self) -> List[str]:
		"""Возвращает список всех зарегистрированных функций"""
		return list(self._functions.keys())

	def execute(self, function_name: str, arguments: Dict[str, Any]) -> str:
		"""
		Выполняет функцию с переданными аргументами.

		Args:
			function_name: Имя функции из реестра
			arguments: Аргументы для функции

		Returns:
			Результат выполнения функции
		"""
		func = self.get_function(function_name)
		return func(arguments)

	def _validate_function_signature(self, func: Callable):
		"""Проверяет сигнатуру функции"""
		sig = inspect.signature(func)
		params = list(sig.parameters.values())

		if len(params) != 1:
			raise ValueError(
				f"Функция {func.__name__} должна принимать ровно 1 аргумент "
				f"(получено {len(params)}): {sig}"
			)

		# Проверяем аннотацию типа для аргумента
		param = params[0]
		if param.annotation != inspect.Parameter.empty:
			# Проверяем, что аннотация - Dict или dict
			ann_str = str(param.annotation)
			if "Dict" not in ann_str and "dict" not in ann_str:
				raise ValueError(
					f"Аргумент функции {func.__name__} должен быть Dict или dict, "
					f"получено: {param.annotation}"
				)

	def _validate_schema(self, schema: Dict[str, Any], func_name: str):
		"""Базовая валидация JSON-схемы"""
		required_fields = ["name", "description", "parameters"]

		for field in required_fields:
			if field not in schema:
				raise ValueError(f"Схема для {func_name} не содержит обязательное поле '{field}'")

		if schema["name"] != func_name:
			raise ValueError(
				f"Имя в схеме '{schema['name']}' не соответствует имени функции '{func_name}'"
			)

		# Проверяем структуру parameters
		params = schema["parameters"]
		if not isinstance(params, dict):
			raise ValueError(f"Поле 'parameters' должно быть словарем, получено {type(params)}")

		if "type" not in params or params["type"] != "object":
			raise ValueError("Поле 'parameters.type' должно быть 'object'")

		if "properties" not in params:
			raise ValueError("Схема должна содержать 'parameters.properties'")


# Глобальный экземпляр реестра (синглтон)
_registry = FunctionRegister()


def get_registry() -> FunctionRegister:
	"""Возвращает глобальный экземпляр реестра"""
	return _registry


def register_function(
		function: Callable[[Dict[str, Any]], str],
		schema: Dict[str, Any],
		name: Optional[str] = None,
		description: Optional[str] = None
) -> str:
	"""Декоратор для регистрации функции"""
	return _registry.register_function(function, schema, name, description)


def function(schema: Dict[str, Any], name: Optional[str] = None):
	"""Декоратор для регистрации функции"""

	def decorator(func: Callable[[Dict[str, Any]], str]):
		_registry.register_function(func, schema, name or func.__name__)
		return func

	return decorator