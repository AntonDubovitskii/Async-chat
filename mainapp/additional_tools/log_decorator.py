import inspect
import logging


def log(func):
    def wrapper(*args, **kwargs):
        s = func(*args, **kwargs)
        # Определяем название файла в котором находится декорируемая функция
        pyfile = inspect.getfile(func).split("/")[-1]

        func_name_info = f'Вызвана функция {func.__name__} с параметрами {args}, {kwargs}'
        upper_func_info = f'Функция {func.__name__}() вызвана из функции {inspect.stack()[1][3]}'
        # В зависимости от файла выбираем правильный логгер, если файл не из проекта, то просто выводим в консоль
        match pyfile:
            case 'console_client.py':
                logger = logging.getLogger('client')
            case 'server_old.py':
                logger = logging.getLogger('server')
            case _:
                print(func_name_info)
                print(upper_func_info)
                return s

        logger.debug(func_name_info)
        logger.debug(upper_func_info)

        return s

    return wrapper
