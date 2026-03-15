import argparse
import json
import sys

import yaml

from src.schema.client_schema import ClientModel
from src.schema.json_schema import Schema

sys.tracebacklimit = 0


def on_traceback():
    sys.tracebacklimit = 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--func", type=str, required=True)
    parser.add_argument("--schema", type=str, required=True)
    parser.add_argument("--conf", type=str, required=True)
    args: argparse.Namespace = parser.parse_args()

    if args.trace:
        on_traceback()

    with open(args.schema, encoding="utf-8") as f:
        schema_dict = json.load(f)
    schema = Schema.model_validate(schema_dict)

    with open(args.conf, encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)
    conf = ClientModel.model_validate(**args.conf)

    # module = import_module(import_path)
    # func = getattr(module, file.stem)

    # sig = inspect.signature(func)

    # source = inspect.getsource(func)

    # data = {
    #     "arguments": sig.parameters,
    #     "json_schema": schema,
    #     "source_code": source,
    # }

    # FunctionSchema.model_validate(data)


if __name__ == "__main__":
    main()
