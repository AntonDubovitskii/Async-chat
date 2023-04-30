import logging

import time
from datetime import datetime

logger = logging.getLogger('client')


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


def generate_common_chat_message(message, account_name='Guest', current_datetime=None):
    """
    Формирование словаря с msg-сообщением, который далее будет переведен
    в формат json и отправлен на сервер
    """
    message = {
        "action": "msg",
        "time": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        "from": account_name,
        "message": message
    }
    return message


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
