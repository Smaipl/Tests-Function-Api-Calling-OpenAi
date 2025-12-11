from src.function_register import FunctionRegistry

ADD_SCHEMA = {
    "name": "add_num",
    "description": "Выполняет сложение числа с 1",
    "parameters": {
        "type": "object",
        "properties": {
            "num1": {
                "type": "integer", "description": "Число для сложения"
            },
            "num2": {
                "type": "integer", "description": "Число для сложения"
            }
        },
        "required": ["num1", "num2"],
    },
}


@FunctionRegistry.function(ADD_SCHEMA)
def add_num(arguments: dict)-> str:
    return str(abs(arguments["num1"]) + abs(arguments["num2"]))
