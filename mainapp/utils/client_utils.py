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


def generate_common_chat_message(message, account_name='Guest', destination='#', current_datetime=None):
    """
    Формирование словаря с msg-сообщением, который далее будет переведен
    в формат json и отправлен на сервер
    """
    message_dict = {
        "action": "msg",
        "time": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        "from": account_name,
        "to": destination,
        "message": message
    }
    return message_dict

