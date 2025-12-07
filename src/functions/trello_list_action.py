import sys
import os

# Добавляем родительскую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

from config import API_KEY_TRELLO, API_TOKEN_TRELLO
from src.function_register import get_registry, function


# Получаем реестр
registry = get_registry()


TRELLO_LIST_ACTION_SCHEMA={
  "name": "trello_list_action",
  "description": "Выполняет действия над списками Trello: создание, получение и обновление. Универсальный маршрутизатор для Trello API.",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "Тип действия над списком Trello.",
        "enum": ["create", "get", "update"]
      },
      "id_board": {
        "type": "string",
        "description": "ID доски Trello. Используется для create и update."
      },
      "name_board": {
        "type": "string",
        "description": "Имя доски Trello, если неизвестен id_board."
      },
      "id_list": {
        "type": "string",
        "description": "ID списка Trello. Используется для get и update."
      },
      "name_list": {
        "type": "string",
        "description": "Имя списка Trello, если неизвестен id_list."
      },
      "new_name_list": {
        "type": "string",
        "description": "Новое имя списка. Используется при create и update."
      },
      "closed": {
        "type": "string",
        "description": "Архивировать (true) или разархивировать (false) список.",
        "enum": ["true", "false"]
      },
      "api_key_trello": {
        "type": "string",
        "description": "Ключ доступа Trello API. Может быть передан явно или подтянут из окружения."
      },
      "api_token_trello": {
        "type": "string",
        "description": "Токен доступа Trello API. Может быть передан явно или подтянут из окружения."
      }
    },
    "required": ["action"]
  }
}

@function(TRELLO_LIST_ACTION_SCHEMA)
def trello_list_action(arguments: dict) -> str:
    """
    Выполняет действия над списками Trello: создание, получение и обновление.
    Функция работает как универсальный маршрутизатор: в зависимости от значения параметра "action"
    формируется запрос к соответствующему endpoint Trello API.

    Особенности:
            - Поддерживает одиночное обращение: к 1-му листу из 1-й доски.
            - Если неизвестно id Board и/или id List, поиск и вытягивание нужного id производится с Api Trello Members
            c endpoint members/me
            -Если есть несколько одинаковых досок/листов по имени, можно указать позицию листа 1,2,5.
            Если будет неверная позиция будет взят 1-й доска/лист из найденных.
            Если указано не будет позиция, по умолчанию берется 1-я из найденных.

    Авторизация:
            - Для работы функции требуется ключ и токен Trello API.
            - Они загружаются из переменных окружения и доступны в коде как:
                    - API_KEY_TRELLO = os.getenv("API_KEY_TRELLO")
                    - API_TOKEN_TRELLO = os.getenv("API_TOKEN_TRELLO")
            - Эти значения автоматически добавляются в каждый запрос.
            - При отсутствии ключа/токена запросы будут отклоняться.

    Поддерживаемые действия (action):
            - "create": Создать новый список.
                    Endpoint: POST /lists
                    Обязательные параметры:
                            - id_board (str): ID доски.
                            - new_name_list (str): Имя нового списка.

            - "get": Получить информацию о списке.
                    Endpoint: GET /lists/{id_list}
                    Обязательные параметры:
                            - id_list (str): ID списка.

            - "update": Обновить список.
                    Endpoint: PUT /lists/{id_list}
                    Обязательные параметры:
                            - id_list (str): ID списка.
                    Дополнительные параметры:
                            - new_name_list (str): Новое имя списка.
                            - id_board (str): ID доски, если нужно переместить список.
                            - closed (str): "true" — архивировать, "false" — разархивировать.

    Аргументы:
            arguments (dict): Словарь с параметрами запроса.
                    - action (str, обязательно): Тип действия ("create", "get", "update").
                    - id_board (str): ID доски (для "create", опционально для "update").
                    - name_board (str): Имя Доски если неизвестен id_board.
                    - id_list (str): ID списка (для "get" и "update").
                    - name_list (str): Имя списка (если неизвестен id_list).
                    - new_name_list (str): Новое имя списка (для "action", "update").
                    - closed (str): Архивировать или разархивировать список (для "update").

    Возвращает:
            str: JSON-строка с результатом запроса.
                    - При успешном запросе: данные, полученные от Trello API (созданный список,
                      информация о списке, результат обновления).
                    - При ошибке: объект с ключами:
                            - "error": описание ошибки
                            - "status": HTTP-код
                            - "body": текст ответа сервера.
    """

    import json
    import requests
    from typing import Optional, Dict, List

    import os
    from dotenv import load_dotenv

    load_dotenv()

    # --- Класс исключений ---
    class TrelloListError(Exception):
        pass

    API_KEY_TRELLO = arguments.get("api_key_trello") or os.getenv("API_KEY_TRELLO")
    API_TOKEN_TRELLO = arguments.get("api_token_trello") or os.getenv(
        "API_TOKEN_TRELLO"
    )

    if not API_KEY_TRELLO:
        raise TrelloListError(
            json.dumps(
                {"error": "Missing 'API_KEY_TRELLO not found'"}, ensure_ascii=False
            )
        )
    if not API_TOKEN_TRELLO:
        raise TrelloListError(
            json.dumps(
                {"error": "Missing 'API_TOKEN_TRELLO not found'"}, ensure_ascii=False
            )
        )

    class TrelloHelper:
        @staticmethod
        def get_boards(name_board: str) -> Dict:
            if not name_board:
                raise TrelloListError(
                    json.dumps({"error": "Missing 'name_board'"}, ensure_ascii=False)
                )

            url = "https://api.trello.com/1/members/me"
            params = {
                "key": API_KEY_TRELLO,
                "token": API_TOKEN_TRELLO,
                "boards": "all",
                "board_lists": "all",
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            res = response.json()["boards"]

            board = next(
                (
                    {
                        "id": b["id"],
                        "name": b["name"],
                        "lists": [
                            {"id": l["id"], "name": l["name"], "pos": l["pos"]}
                            for l in b.get("lists", [])
                        ],
                    }
                    for b in res
                    if b["name"] == name_board
                ),
                None,
            )

            if not board:
                raise TrelloListError(
                    json.dumps(
                        {"error": f"Board '{name_board}' not found"}, ensure_ascii=False
                    )
                )

            return board

        @staticmethod
        def get_lists(name_list: str, id_board: str, lists: List) -> Dict:
            if not name_list:
                raise TrelloListError(
                    json.dumps({"error": "Missing 'name_list'"}, ensure_ascii=False)
                )

            if not id_board:
                raise TrelloListError(
                    json.dumps({"error": "Missing 'id_board'"}, ensure_ascii=False)
                )

            if not lists:
                raise TrelloListError(
                    json.dumps(
                        {"error": f"Lists not found in {id_board}"}, ensure_ascii=False
                    )
                )

            flist = next((l for l in lists if l["name"] == name_list), None)
            if not flist:
                raise TrelloListError(
                    json.dumps(
                        {"error": f"List '{name_list}' not found"}, ensure_ascii=False
                    )
                )

            # get_one_list = lambda l, c: (l[count_list - 1] if c is not None and 0 <= c - 1 < len(l) else l[0])

            # if count_list is not None:
            #     lists: List = get_one_list(lists, count_list)

            return flist
            # return lists[count_list if count_list < len(lists) else 0]

        # Функция отправки запроса
        @staticmethod
        def send(method: str, url: str, params=None, data=None) -> dict:
            if params:
                params = {k: v for k, v in params.items() if v is not None}
            if data:
                data = {k: v for k, v in data.items() if v is not None}

            response = requests.request(method, url, params=params, data=data)
            try:
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {
                    "error": str(e),
                    "status": response.status_code,
                    "body": response.text,
                }

    #           -----------------------------------------------------------------------------------------------            #

    action: Optional[str] = arguments.get("action")
    if action is None or action not in {"create", "get", "update"}:
        raise TrelloListError(
            json.dumps(
                {"error": f"Unknown or missing action '{action}'"}, ensure_ascii=False
            )
        )

    base_url = "https://api.trello.com/1/lists"

    # --- Проверки на отсутствие обязательных аргументов ---
    if action == "create":
        if not arguments.get("id_board") and not arguments.get("name_board"):
            raise TrelloListError(
                json.dumps(
                    {"error": "Missing 'id_board' or 'name_board' for create"},
                    ensure_ascii=False,
                )
            )
        if not arguments.get("new_name_list"):
            raise TrelloListError(
                json.dumps(
                    {"error": "Missing 'new_name_list' for create"},
                    ensure_ascii=False,
                )
            )

    elif action in ["get", "update"]:
        if not arguments.get("id_list") and not arguments.get("name_list"):
            raise TrelloListError(
                json.dumps(
                    {"error": f"Missing 'id_list' or 'name_list' for {action}"},
                    ensure_ascii=False,
                )
            )

    id_board = arguments.get("id_board")
    name_board = arguments.get("name_board")
    id_list = arguments.get("id_list")
    name_list = arguments.get("name_list")
    board = None

    if not id_board and name_board:
        board = TrelloHelper.get_boards(name_board=arguments.get("name_board"))
        id_board = board["id"]

    if not id_board:
        raise TrelloListError(
            json.dumps({"error": f"не удалось вытянуть id Доски"}, ensure_ascii=False)
        )

    if action in ["get", "update"]:
        if not id_list and name_list:
            lists = board["lists"]
            id_list = TrelloHelper.get_lists(
                name_list=arguments.get("name_list"), id_board=id_board, lists=lists
            )["id"]

        if not id_list:
            raise TrelloListError(
                json.dumps(
                    {"error": f"не удалось вытянуть id Списка"}, ensure_ascii=False
                )
            )

    action_url = f"{base_url}/{id_list}"

    # Маршруты по действиям
    routes = {
        "create": {
            "method": "POST",
            "url": base_url,
            "params": {
                "name": arguments.get("new_name_list"),
                "idBoard": id_board,
                "key": API_KEY_TRELLO,
                "token": API_TOKEN_TRELLO,
            },
        },
        "get": {
            "method": "GET",
            "url": action_url,
            "params": {
                "cards": "all",
                "card_fields": "id,name",
                "fields": "id,name,idBoard",
                "actions": "all",
                "action_fields": "id,type,date,data",
                "key": API_KEY_TRELLO,
                "token": API_TOKEN_TRELLO,
            },
        },
        "update": {
            "method": "PUT",
            "url": action_url,
            "params": {
                "key": API_KEY_TRELLO,
                "token": API_TOKEN_TRELLO,
                "name": arguments.get("new_name_list"),
                "idBoard": id_board,
                "closed": arguments.get("closed"),
            },
        },
    }

    route = routes[action]

    result = TrelloHelper.send(route["method"], route["url"], params=route["params"])

    return json.dumps(result, ensure_ascii=False, indent=2)

SCHEMAS = {
	"trello_list_action": TRELLO_LIST_ACTION_SCHEMA,
}