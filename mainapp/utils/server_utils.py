import time
import logging

from additional_tools.log_decorator import log

logger = logging.getLogger('server')


def process_presence_msg(data: dict):
    """
    Проверка обязательных полей json объекта, необходимых для соответствия протоколу JIM
    и формирование соответствующего словаря для ответа клиенту
    """
    if 'action' in data and 'time' in data and 'user' in data \
            and data['action'] == 'presence' and data['user']['account_name']:
        msg = {
            "response": 200,
            "time": time.time(),
            "alert": f"Привет {data['user']['account_name']}!"
        }
    else:
        msg = {
            "response": 400,
            "time": time.time(),
            "error": "Bad Request"
        }
    return msg
