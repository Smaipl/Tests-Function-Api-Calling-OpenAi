import importlib
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.function_register import get_registry

functions_dir = os.path.join(current_dir, "functions")

if os.path.exists(functions_dir):
    for file in os.listdir(functions_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = f"src.functions.{file[:-3]}"   # <-- ВАЖНО: src.functions
            try:
                importlib.import_module(module_name)
                print(f"📥 Импортирован модуль: {module_name}")
            except Exception as e:
                print(f"❌ Ошибка импорта {module_name}: {e}")

try:
    registry = get_registry()

    print("📋 Проверка реестра функций:")
    print("=" * 40)

    functions = registry.list_functions()

    if not functions:
        print("❌ Реестр пуст! Ни одной функции не зарегистрировано.")
        print("\n🔍 Возможные причины:")
        print("   1. Функции не импортируются")
        print("   2. Нет файлов в src/functions/")
        print("   3. Файлы функций не содержат декоратор @function")
        print("   4. Проблемы с импортами")

        # Проверяем есть ли файлы в src/functions/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        functions_dir = os.path.join(current_dir, "functions")

        if os.path.exists(functions_dir):
            print(f"\n📁 Содержимое папки {functions_dir}:")
            for file in os.listdir(functions_dir):
                if file.endswith('.py'):
                    print(f"   - {file}")
        else:
            print(f"\n❌ Папка {functions_dir} не существует!")

    else:
        print(f"✅ Зарегистрировано функций: {len(functions)}")
        for func_name in functions:
            info = registry.get_function_info(func_name)
            print(f"\n  🎯 {func_name}:")
            print(f"     Описание: {info.description[:50]}...")
            print(f"     Модуль: {info.module}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback

    traceback.print_exc()