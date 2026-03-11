DEFAULT_REQUIRED_FIELDS = ["property_type", "description", "default"]

TYPE_MAPPING = {
    "object": dict,
    "array": list,
    "string": str,
    "number": float | int,
    "integer": int,
    "boolean": bool,
    "null": type(None),
}
