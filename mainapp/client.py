import sys
import time
import logging

sys.path.append("..")

from logs import client_log_config
from socket import *
from mainapp.data_transfer import get_data, send_data
from additional_tools.log_decorator import log

logger = logging.getLogger('client')


@log
def generate_greeting(account_name='Guest'):
    """
    Формирование словаря с presence-сообщением, который далее будет переведен
    в формат json и отправлен на сервер
    """
    message = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {
            "account_name": account_name,
            "status": "I am here!"
        }
    }
    return message


@log
def process_server_answer(data_dict):
    """
    Обработка ответа от сервера на presence-сообщение
    """
    if data_dict['response'] == 200:
        logger.info(f'Server answer to presence message: {data_dict["response"]}')
        return '200 OK'
    elif data_dict['response'] == 400:
        logger.error(f'Server answer to presence message: {data_dict["response"]}')
        return '400 Bad Request'
    else:
        logger.error(f'Server answer to presence message: {data_dict["response"]}')
        return 'Произошла неизвестная ошибка'


def main():
    # Проверка и парсинг параметров командной строки
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 35000
    except ValueError:
        logger.error(f'Port {server_port} was entered. Available ports range from 1024 to 65535.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_address, server_port))

    presence_msg = generate_greeting('Anton_1993')
    send_data(s, presence_msg)

    data_dict = get_data(s)
    process_server_answer(data_dict)

    s.close()


if __name__ == '__main__':

    try:
        main()
    except Exception as e:
        logger.critical(e)
