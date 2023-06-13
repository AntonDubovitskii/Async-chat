import logging
import sys

logger = logging.getLogger('server')


# Дескриптор для описания порта:
class Port:
    """
    Класс дескриптор для номера порта.
    При попытке установить некорректное значение, генерирует исключение.
    """
    def __init__(self, name):
        self.name = name

    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            print(f'Попытка запуска сервера с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            sys.exit(1)
        # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
        instance.__dict__[self.name] = value
