import argparse
import inspect
import json
import sys
from importlib import import_module
from pathlib import Path

import orjson

from src.schema.json_schema import Schema
from src.schema.py_schema import FunctionSchema

sys.tracebacklimit = 0


def parse_json(file) -> Schema:
    with open(file, encoding="utf-8") as f:
        raw_schema = orjson.loads(json.dumps(json.load(f)))

    return Schema.model_validate(raw_schema)


def parse_func(file: Path, schema: Schema) -> bool:
    import_path = ".".join(file.with_suffix("").parts)

    module = import_module(import_path)
    func = getattr(module, file.stem)

    sig = inspect.signature(func)

    source = inspect.getsource(func)

    data = {
        "arguments": sig.parameters,
        "json_schema": schema,
        "source_code": source,
    }

    FunctionSchema.model_validate(data)

    return True


def on_traceback():
    sys.tracebacklimit = 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--py", type=str, required=True)
    parser.add_argument("--json", type=str, required=True)
    args: argparse.Namespace = parser.parse_args()

    if args.trace:
        on_traceback()

    schema = parse_json(args.json)
    path_func = Path(args.py)
    res = parse_func(path_func, schema)

    if not res:
        raise Exception("Неизвестная ошибка")


if __name__ == "__main__":
    main()
