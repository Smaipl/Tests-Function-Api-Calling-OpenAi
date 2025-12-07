import sys
import os

# Добавляем родительскую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

try:
  # Пробуем импортировать из src
  from src.function_register import get_registry, function

  print("✅ Импорт function_registry успешен")

except ImportError as e:
  print(f"❌ Ошибка импорта: {e}")
  sys.exit(1)

# Получаем реестр
registry = get_registry()

YANDEX_METRICA_SCHEMA ={
  "name": "get_report_yandex_metrica_sync",
  "description": "Формирует отчёт из Яндекс.Метрики (Reports API) в синхронном режиме и возвращает результат в виде строки (CSV или JSON). Функция автоматически оптимизирует выгрузку: разбивает длинные периоды на месяцы/кварталы, обрабатывает пагинацию данных",
  "parameters": {
    "type": "object",
    "properties": {
      "ids": {
        "type": "string",
        "description": "ID счётчика Яндекс.Метрики (ОБЯЗАТЕЛЬНЫЙ). Чтобы найти ID: зайдите в Яндекс.Метрику → Настройки → Список счётчиков. ID показан в интерфейсе и в URL: https://metrika.yandex.ru/dashboard?id=12345678"
      },
      "date1": {
        "type": "string",
        "description": "Начальная дата периода в формате ГГГГ-ММ-ДД (например, 2024-09-01). Если пользователь указал только месяц или год - вычисли конкретные даты"
      },
      "date2": {
        "type": "string",
        "description": "Конечная дата периода в формате ГГГГ-ММ-ДД (например, 2024-09-30). Если пользователь сказал 'за последние 7 дней' - рассчитай текущую дату минус 7 дней"
      },
      "metrics": {
        "type": "string",
        "description": "Метрики (цифровые показатели) через запятую. Основные: ym:s:visits (визиты), ym:s:users (пользователи), ym:s:pageviews (просмотры). Дополнительные: ym:s:bounceRate (отказы), ym:s:pageDepth (глубина просмотра), ym:s:avgVisitDurationSeconds (время на сайте). ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ УКАЗАЛ - СПРОСИ КОНКРЕТНЫЕ МЕТРИКИ"
      },
      "dimensions": {
        "type": "string",
        "description": "Группировки (по каким параметрам разбивать данные) через запятую. Основные: ym:s:date (по дням), ym:s:regionCountry (по странам), ym:s:regionCityName (по городам), ym:s:deviceCategory (по устройствам), ym:s:trafficSource (по источникам трафика). ЕСЛИ НЕ ЯСНО - СПРОСИ ПО КАКОМУ ПАРАМЕТРУ ГРУППИРОВАТЬ"
      },
      "filters": {
        "type": "string",
        "description": "Фильтрация данных. МОЖНО фильтровать только по измерениям (dimensions), НЕ по метрикам. Примеры: ym:s:regionCityName=='Москва' (только Москва), ym:s:deviceCategory=='mobile' (только мобильные). ВАЖНО: для стран (ym:s:regionCountry) фильтрация работает ТОЛЬКО по числовым идентификаторам регионов (например, Россия=225, Беларусь=149, Украина=187, США=84, Польша=50). Если пользователь указывает название страны, необходимо перевести его в числовой код, используя справочник регионов Яндекс.Метрики. Например, 'Россия' должно быть преобразовано в '225'. Если пользователь хочет фильтровать по метрикам, объясните, что это невозможно."
      },
      "preset": {
        "type": "string",
        "description": "Готовый предустановленный отчёт для быстрого старта. Используй если пользователь не указал метрики/измерения. Варианты: traffic (общий трафик), sources (источники), geo (география), devices (устройства), demographics (демография). ЕСЛИ ЗАДАНЫ METRICS И DIMENSIONS - PRESET ИГНОРИРУЕТСЯ",
        "enum": ["traffic", "sources", "geo", "devices", "demographics"]
      },
      "sort": {
        "type": "string",
        "description": "Сортировка результатов. Примеры: -ym:s:visits (по убыванию визитов), ym:s:date (по возрастанию даты). МОЖНО УКАЗЫВАТЬ ТОЛЬКО ПОЛЯ, КОТОРЫЕ ПРИСУТСТВУЮТ В METRICS ИЛИ DIMENSIONS"
      },
      "lang": {
        "type": "string",
        "description": "Язык интерфейса для названий параметров",
        "enum": ["ru", "en"],
        "default": "ru"
      },
      "token": {
        "type": "string",
        "description": "OAuth-токен для доступа к приватным счётчикам. Если не указан, используется переменная окружения YANDEX_METRIKA_TOKEN. ЕСЛИ СЧЁТЧИК ПРИВАТНЫЙ И ТОКЕН НЕ УКАЗАН - ОШИБКА АВТОРИЗАЦИИ"
      },
      "timeout": {
        "type": "integer",
        "description": "Общий лимит времени выполнения функции в секундах (по умолчанию 30). Все подзапросы делят этот лимит; если он исчерпан - выполнение прерывается",
        "default": 30
      },
      "batch_size": {
        "type": "integer",
        "description": "Лимит строк на страницу (по умолчанию 5000). API возвращает максимум batch_size строк за один запрос; для больших выборок используется offset",
        "default": 5000
      },
      "max_rows": {
        "type": "integer",
        "description": "Максимальное количество строк для выгрузки (по умолчанию 10000). Даже при использовании offset общее количество строк может быть ограничено самим API",
        "default": 10000
      },
      "output_format": {
        "type": "string",
        "description": "Формат результата: csv (для Excel и таблиц) или json (для разработчиков и интеграций)",
        "enum": ["csv", "json"],
        "default": "csv"
      }
    },
    "required": ["ids", "date1", "date2"]
  }
}

@function(YANDEX_METRICA_SCHEMA)
def get_report_yandex_metrica_sync(arguments: dict) -> str:
  """
  Формирует отчёт из Яндекс.Метрики (Reports API) в синхронном режиме
  и возвращает результат в виде строки (CSV или JSON).

  Args:
	  arguments (dict): словарь параметров.

	  Основные параметры (боевые, соответствуют API Метрики):
		  - ids (str): ID счётчика (**обязательный**).
		  - date1 (str, формат YYYY-MM-DD): начальная дата периода.
		  - date2 (str, формат YYYY-MM-DD): конечная дата периода.
		  - metrics (str, optional): список метрик через запятую.
		  - dimensions (str, optional): список группировок через запятую.
		  - filters (str, optional): строка фильтрации.
		  - preset (str, optional): название предустановленного отчёта.
		  - sort (str, optional): поле сортировки (например "-ym:s:pageviews").
		  - lang (str, optional): язык интерфейса (по умолчанию "en").
		  - token (str, optional): OAuth‑токен.

	  Надстройки / тестовые параметры (служебные, не являются частью API, а управляют логикой выгрузки):
		  - split (bool, optional): включить авто‑дробление диапазона дат (по умолчанию True).
		  - timeout (int, optional): общий лимит времени выполнения функции в секундах (по умолчанию 60).
			  • Все подзапросы делят этот лимит; если он исчерпан — выполнение прерывается.
		  - batch_size (int, optional): лимит строк на страницу (по умолчанию 5000).
		  - max_rows (int, optional): максимальное количество строк для выгрузки (10 000).
		  - output_format (str, optional): формат результата: "csv" или "json" (по умолчанию "csv").

  Returns:
	  str: результат отчёта в формате CSV или JSON (в зависимости от параметра output_format).

  Замечания:
	  * Если заданы metrics и dimensions — они перекрывают preset (работает ручной режим).
	  * В параметре filters можно использовать только dimensions, метрики там не поддерживаются.
	  * В параметре sort можно указывать только поля, которые реально присутствуют в metrics или dimensions.
	  * API возвращает максимум batch_size !> 100 000 строк за один запрос; для больших выборок используется offset.
	  * Даже при использовании offset общее количество строк может быть ограничено самим API.
	  * Множественные периоды (comparisonMode) не поддерживаются.
	  * Если API возвращает метрики как вложенные списки ([[...]]),
		функция обрабатывает только первый массив значений.
		Поддержка нескольких наборов метрик (например, при сравнении периодов) не реализована.
	  * Параметры split, timeout, batch_size, max_rows и output_format являются надстройками функции
		и не поддерживаются напрямую API Метрики.
	  * Если счётчик приватный и токен не указан — запрос завершится ошибкой авторизации.
	  * Если счётчик публичный — можно работать без токена.
	  * Таймаут контролируется глобально: все подзапросы делят один общий лимит времени.

  """

  # def upload_to_tmpfiles(df: pd.DataFrame, output_format: str = "csv") -> str:
  #   """
  # 	Сохраняет DataFrame во временный файл и загружает его на tmpfiles.org
  # 	"""
  #
  # def fetch_chunk_all_pages_streaming(url, params, headers, batch_size, output_format="csv", file_path="report.csv"):
  #   """
  # 	Стриминговая выгрузка: постранично пишет результат в файл (CSV или NDJSON),
  # 	не накапливая все строки в памяти.
  # 	"""

  import os
  import requests
  import pandas as pd
  import json
  import time
  from datetime import datetime, timedelta

  # --- Класс исключений ---
  class YandexMetrikaError(Exception):
    """Специализированное исключение для ошибок работы с API Яндекс.Метрики"""
    pass

  API_URL = "https://api-metrika.yandex.net/stat/v1/data"
  MAX_ROWS = 10000
  BATCH_SIZE = 5000
  TIME_OUT = 30
  start_time = time.perf_counter()  # ⏱ старт замера общего времени выполнения
  global_timeout = int(arguments.get("timeout", TIME_OUT))  # общий лимит времени на всю функцию

  # --- Функция вычисления остатка времени ---
  def remaining_timeout() -> float:
    """
	Возвращает количество секунд, оставшихся до истечения глобального лимита.
	Если лимит исчерпан — выбрасывает исключение.
	"""
    elapsed = time.perf_counter() - start_time
    left = global_timeout - elapsed
    if left <= 0:
      raise YandexMetrikaError("Превышен общий лимит времени на выполнение запроса")
    return left

  # --- Разбиение диапазона дат на чанки ---
  def auto_date_chunks(date1: str, date2: str, split: bool = True):
    """
	Делит диапазон дат на оптимальные чанки:
	  - до 365 дней → месяцы
	  - до 5 лет → кварталы
	  - больше 5 лет → годы
	"""
    try:
      start = datetime.strptime(date1, "%Y-%m-%d")
      end = datetime.strptime(date2, "%Y-%m-%d")
    except ValueError as e:
      raise YandexMetrikaError(f"Неверный формат даты: {e}")

    if start > end:
      raise YandexMetrikaError("date1 не может быть больше date2")

    if not split:
      yield date1, date2
      return

    delta_days = (end - start).days

    # до 1 года → месяцы
    if delta_days <= 365:
      while start <= end:
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        chunk_end = min(next_month - timedelta(days=1), end)
        yield start.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
        start = next_month

    # до 5 лет → кварталы
    elif delta_days <= 1825:
      while start <= end:
        # вычисляем начало следующего квартала
        month = ((start.month - 1) // 3 + 1) * 3 + 1
        year = start.year
        if month > 12:
          month = 1
          year += 1
        next_quarter = datetime(year, month, 1)
        chunk_end = min(next_quarter - timedelta(days=1), end)
        yield start.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
        start = next_quarter

    # больше 5 лет → годы
    else:
      while start <= end:
        next_year = start.replace(month=1, day=1, year=start.year + 1)
        chunk_end = min(next_year - timedelta(days=1), end)
        yield start.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")
        start = next_year

  # --- Построение DataFrame из ответа API ---
  def build_dataframe(data: dict) -> pd.DataFrame:
    """
	Преобразует JSON-ответ API в pandas.DataFrame.
	Корректно обрабатывает вложенные массивы metrics.
	"""
    query = data.get("query", {}) or {}
    dim_names = [d.split(":")[-1] for d in query.get("dimensions", [])]
    met_names = [m.split(":")[-1] for m in query.get("metrics", [])]

    rows = []
    for row in data.get("data", []):
      record = {}
      # Обработка dimensions
      for j, dim in enumerate(row.get("dimensions", [])):
        record[dim_names[j] if j < len(dim_names) else f"dimension_{j}"] = dim.get("name")

      # Обработка metrics (учёт вложенных списков)
      metrics = row.get("metrics", [])
      if metrics and isinstance(metrics[0], list):
        metrics = metrics[0]

      for j, val in enumerate(metrics):
        record[met_names[j] if j < len(met_names) else f"metric_{j}"] = val

      rows.append(record)

    return pd.DataFrame(rows, columns=dim_names + met_names)

  # --- Запрос страницы ---
  def fetch_page(url, params, headers):
    resp = None
    try:
      resp = requests.get(url, params=params, headers=headers, timeout=remaining_timeout())
      resp.raise_for_status()
      return resp.json()
    except requests.exceptions.Timeout:
      raise YandexMetrikaError("Превышен общий лимит времени (timeout)")
    except requests.exceptions.ConnectionError:
      raise YandexMetrikaError("Ошибка соединения с API Яндекс.Метрики")
    except requests.exceptions.HTTPError:
      if resp is not None:
        try:
          error_json = resp.json()
          message = (
                  error_json.get("message")
                  or error_json.get("errors", [{}])[0].get("message", "")
          )
        except Exception:
          message = resp.text
        code = resp.status_code
        if code == 400:
          raise YandexMetrikaError(f"[400] Неверные параметры запроса: {message}")
        elif code == 401:
          raise YandexMetrikaError(f"[401] Неавторизован: {message}")
        elif code == 402:
          raise YandexMetrikaError(f"[402] Превышена квота или требуется оплата: {message}")
        elif code == 403:
          raise YandexMetrikaError(f"[403] Доступ запрещён: {message}")
        elif code == 404:
          raise YandexMetrikaError(f"[404] Счётчик или ресурс не найден: {message}")
        elif code == 413:
          raise YandexMetrikaError(f"[413] Слишком большой запрос: {message}")
        elif code == 429:
          raise YandexMetrikaError(f"[429] Превышен лимит запросов: {message}")
        elif code >= 500:
          raise YandexMetrikaError(f"[{code}] Ошибка сервера: {message}")
        else:
          raise YandexMetrikaError(f"[{code}] Неизвестная ошибка API: {message}")
      else:
        raise YandexMetrikaError("HTTPError, но объект ответа не создан")
    finally:
      time.sleep(0.11)

  def fetch_chunk_all_pages(url, params, headers, batch_size, max_rows=None):
    """
	Загружает все страницы данных (limit+offset) для заданного диапазона дат.
	Учитывает total_rows и sampled из ответа API.
	"""
    all_rows = []
    offset = 1
    query = None
    total_rows = None
    sampled_global = False

    while True:
      p = params.copy()
      p.update({"limit": batch_size, "offset": offset})
      payload = fetch_page(url, p, headers)

      if "data" not in payload:
        raise YandexMetrikaError(f"Некорректный ответ API при offset={offset}: {payload}")

      if query is None:
        query = payload.get("query", {})

      # читаем total_rows и sampled
      total_rows = payload.get("total_rows", total_rows)
      if payload.get("sampled"):
        sampled_global = True

      data_rows = payload.get("data", []) or []
      all_rows.extend(data_rows)

      # проверка max_rows
      if max_rows and len(all_rows) >= max_rows:
        print(f"Достигнут лимит max_rows={max_rows}, обрезаем результат")
        all_rows = all_rows[:max_rows]
        break

      if len(data_rows) < batch_size:
        break

      offset += batch_size

    if sampled_global:
      print("⚠️ Данные усечены (sampled=True) — отчёт может быть неполным")

    return {"query": query, "data": all_rows}

  # --- Валидация входных параметров ---
  if not arguments.get("ids"):
    raise YandexMetrikaError("Не найден параметр 'ids'")
  if not arguments.get("date1") or not arguments.get("date2"):
    raise YandexMetrikaError("Не заданы даты (date1/date2)")

  # --- Подготовка параметров запроса ---
  metrics, dimensions, filters = arguments.get("metrics"), arguments.get("dimensions"), arguments.get("filters")
  preset, sort = arguments.get("preset"), arguments.get("sort")
  lang = arguments.get("lang", "en")
  token = arguments.get("token") or os.getenv("YANDEX_METRIKA_TOKEN")
  split = arguments.get("split", True)
  batch_size = int(arguments.get("batch_size", BATCH_SIZE))
  max_rows = int(arguments.get("max_rows", 0)) or MAX_ROWS
  output_format = arguments.get("output_format", "csv")

  use_manual_config = bool(metrics and dimensions)
  params = {"ids": arguments["ids"], "lang": lang, "date1": arguments["date1"], "date2": arguments["date2"]}

  if use_manual_config:
    # Преобразуем строки в списки, убираем пробелы и пустые элементы
    if isinstance(metrics, str):
      params["metrics"] = [m.strip() for m in metrics.split(",") if m.strip()]
    else:
      params["metrics"] = metrics

    if isinstance(dimensions, str):
      params["dimensions"] = [d.strip() for d in dimensions.split(",") if d.strip()]
    else:
      params["dimensions"] = dimensions

    # Фильтры передаются как строка (API принимает именно строку)
    if filters:
      params["filters"] = filters
  else:
    # Если metrics/dimensions не заданы — используем готовый пресет
    params["preset"] = preset or "traffic"

  if sort:
    params["sort"] = sort

  headers = {}
  if token:
    headers["Authorization"] = f"OAuth {token}"

  # --- Основная логика выгрузки ---
  # Разбиваем общий диапазон дат на чанки (недели/месяцы/годы)
  date_chunks = list(auto_date_chunks(params["date1"], params["date2"], split=split))
  if not date_chunks:
    raise YandexMetrikaError("Не удалось сформировать диапазоны дат для запроса")

  all_rows, query = [], None

  # Проходим по каждому диапазону дат
  for d1, d2 in date_chunks:
    chunk_params = params.copy()
    chunk_params.update({"date1": d1, "date2": d2})

    # Загружаем все страницы данных для текущего диапазона
    payload = fetch_chunk_all_pages(API_URL, chunk_params, headers, batch_size, max_rows)

    # Сохраняем query (структуру запроса) только один раз
    if query is None:
      query = payload.get("query", {})

    # Добавляем строки в общий список
    all_rows.extend(payload.get("data", []))

    # Если достигнут общий лимит строк — останавливаем выгрузку
    if max_rows and len(all_rows) >= max_rows:
      print(f"Достигнут общий лимит max_rows={max_rows}, остановка выгрузки")
      all_rows = all_rows[:max_rows]
      break

  # Если данных нет — выбрасываем исключение
  if not all_rows:
    raise YandexMetrikaError("API вернул пустой результат — данных нет по заданным параметрам")

  # Преобразуем результат в DataFrame
  df = build_dataframe({"data": all_rows, "query": query})

  # Замеряем общее время выполнения
  elapsed = time.perf_counter() - start_time

  mem_bytes = df.memory_usage(deep=True).sum()
  if mem_bytes < 1024:
    mem_str = f"{mem_bytes} Б"
  elif mem_bytes < 1024 * 1024:
    mem_str = f"{mem_bytes / 1024:.2f} КБ"
  elif mem_bytes < 1024 * 1024 * 1024:
    mem_str = f"{mem_bytes / (1024 * 1024):.2f} МБ"
  else:
    mem_str = f"{mem_bytes / (1024 * 1024 * 1024):.2f} ГБ"

  print(
    f"Финальная сводка: строк={len(df)}, "
    f"время={elapsed:.2f} сек, "
    f"память={mem_str}"
  )

  # Возвращаем результат в нужном формате
  if output_format == "json":
    return df.to_json(orient="records", force_ascii=False)
  else:
    return df.to_csv(index=False)

SCHEMAS = {
    "get_report_yandex_metrica_sync": YANDEX_METRICA_SCHEMA,
}