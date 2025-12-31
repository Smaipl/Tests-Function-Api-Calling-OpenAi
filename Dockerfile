FROM python:3.12-slim

WORKDIR /app

# Установим uv
RUN pip install uv

# Скопируем зависимости
COPY pyproject.toml requirements.txt* ./

# Установим зависимости
RUN uv sync || true

# Скопируем код
COPY . .

CMD ["python", "test_runner.py"]
