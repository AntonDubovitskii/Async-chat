import time
import logging

from additional_tools.log_decorator import log

logger = logging.getLogger('server')


def identify_msg_type(data: dict):
    """
    Проверка типа пришедшего сообщения
    :param data:
    :return:
    """
    if not isinstance(data, dict):
        raise ValueError

    if 'action' in data and 'time' in data and 'user' in data \
            and data['action'] == 'presence' and data['user']['account_name']:
        msg_type = 'presense_msg'
    elif 'action' in data and 'time' in data and 'from' in data and 'to' in data and 'message' in data \
            and data['action'] == 'msg' and data['to'] == '#':
        msg_type = 'common_chat_msg'
    elif 'action' in data and 'time' in data and 'from' in data and 'to' in data and 'message' in data \
            and data['action'] == 'msg' and data['to'] != '#':
        msg_type = 'p2p_chat_msg'
    else:
        msg_type = 'incorrect message'

    return msg_type


def generate_presence_answer(data: dict):
    if not isinstance(data, dict):
        raise ValueError
    msg = {
        "response": 200,
        "time": time.time(),
        "alert": f"Привет {data['user']['account_name']}!"
    }
    return msg


def generate_no_user_error_msg(data: dict):
    if not isinstance(data, dict):
        raise ValueError
    msg = {
        "response": 404,
        "time": time.time(),
        "error": f"Ошибка 404! Пользователь {data['to']} не зарегистрирован"
    }
    return msg


def generate_user_not_online_error_msg(data: dict):
    if not isinstance(data, dict):
        raise ValueError
    msg = {
        "response": 410,
        "time": time.time(),
        "error": f"Ошибка 410! Пользователь {data['to']} не в сети"
    }
    return msg
