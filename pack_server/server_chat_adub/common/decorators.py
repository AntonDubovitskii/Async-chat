import inspect
import logging
import sys
import socket

from logs import client_log_config
from logs import server_log_config

sys.path.append('../')


def log(func):
    """
    Декоратор, выполняющий логирование вызовов функций.
    Сохраняет события типа debug, содержащие
    информацию об имени вызываемой функиции, параметры с которыми
    вызывается функция, и модуль, вызывающий функцию.
    """

    def wrapper(*args, **kwargs):
        s = func(*args, **kwargs)
        # Определяем название файла в котором находится декорируемая функция
        pyfile = inspect.getfile(func).split("/")[-1]

        func_name_info = f'Вызвана функция {func.__name__} с параметрами {args}, {kwargs}'
        upper_func_info = f'Функция {func.__name__}() вызвана из функции {inspect.stack()[1][3]}'
        # В зависимости от файла выбираем правильный логгер, если файл не из проекта, то просто выводим в консоль
        match pyfile:
            case 'client.py':
                logger = logging.getLogger('client')
            case 'server.py':
                logger = logging.getLogger('server')
            case _:
                print(func_name_info)
                print(upper_func_info)
                return s

        logger.debug(func_name_info)
        logger.debug(upper_func_info)

        return s

    return wrapper


def login_required(func):
    """
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError.
    """

    def checker(*args, **kwargs):

        from server.server_core import ServerMsgProc
        if isinstance(args[0], ServerMsgProc):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if 'action' in arg and arg['action'] == 'presence':
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
