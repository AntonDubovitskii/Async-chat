from socket import *

from utils.data_transfer import get_data


def create_read_mode_socket(addr):
    """
    Функция реализует функционал клиента в режиме чтения
    :param addr:
    :return:
    """

    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.connect(addr)
        while True:
            try:
                data = get_data(sock)
                print(f"{data['time']} - {data['from']} : {data['message']}")
            except Exception as e:
                print('Сервер недоступен!')
                sock.close()
                break