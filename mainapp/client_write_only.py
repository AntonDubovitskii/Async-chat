from socket import *

from utils.client_utils import generate_common_chat_message
from utils.data_transfer import send_data


def create_write_mode_socket(addr, name='Guest'):
    """
    Функция реализует функционал клиента в режиме записи
    :param addr:
    :return:
    """
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.connect(addr)
        while True:
            msg = input('Ваше сообщение: ')
            if msg == 'exit':
                break
            try:
                dict_msg = generate_common_chat_message(msg, name)
                send_data(sock, dict_msg)
            except Exception:
                print('Сервер недоступен!')
                sock.close()
                break