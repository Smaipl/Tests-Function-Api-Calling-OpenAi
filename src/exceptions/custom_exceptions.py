import json


class BaseJsonException(Exception):
    def __init__(self, message: str = "", fields: any = None):
        self.message = message
        self.fields = fields or []
        super().__init__(self.message)

    def __str__(self):
        details = json.dumps(self.fields, indent=4, ensure_ascii=False)
        return f"\n❌ {self.message}\nДетали: {details}"


class EmptyRequiredFields(BaseJsonException):
    pass


class TypeMismatchJsonToPython(BaseJsonException):
    pass
