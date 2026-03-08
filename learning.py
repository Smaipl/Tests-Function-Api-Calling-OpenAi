import argparse
import inspect
import json
from importlib import import_module
from pprint import pprint
from typing import Any

import orjson

from src.schema.json_schema import Schema

python_to_json: dict[str | tuple, str] = {
    "dict": "object",
    ("list", "tuple"): "array",
    "str": "string",
    ("int", "float"): "number",
    "True": "true",
    "False": "false",
    "None": "null",
}


def parse_json(file):
    with open(file, encoding="utf-8") as f:
        raw_schema = orjson.loads(json.dumps(json.load(f)))

    schema = Schema.model_validate(raw_schema)

    pprint(schema)


def parse_func(file: str):
    name_file: str = file.split(".")[0]
    module = import_module(f"{name_file}")

    func: Any
    try:
        func = getattr(module, f"{name_file}")
    except ValueError:
        return "Неверное "
    sig = inspect.signature(func)

    print(sig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--py", type=str)
    parser.add_argument("--json", type=str)
    args: argparse.Namespace = parser.parse_args()

    parse_json(args.json)


if __name__ == "__main__":
    main()
