from src.function_register import FunctionRegistry

SQRT_SCHEMA = {
    "name": "sqrt_num",
    "description": "Вычисляет положительный квадратный корень числа",
    "parameters": {
        "type": "object",
        "properties": {"num": {"type": "integer", "description": "Число для извлечения корня"}},
        "required": ["num"],
    },
}


@FunctionRegistry.function(SQRT_SCHEMA)
def sqrt_num(arguments: dict)-> str:
    import math

    return str(math.sqrt(arguments["num"]))
