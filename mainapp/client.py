import sys

from socket import *
from threading import Thread
from utils.client_utils import *
from utils.data_transfer import get_data, send_data
from logs import client_log_config
from errors import *


logger = logging.getLogger('client')


def get_server_invitation(sock, username):
    """
    Выполняет процедуру обмена приветствиями с сервером
    :param sock:
    :param username:
    :return:
    """
    greeting = generate_greeting(username)
    send_data(sock, greeting)

    answer_dict = get_data(sock)

    if answer_dict['response'] == 200:
        logger.info(f'Server answer to presence message: {answer_dict["response"]}')
        return '200 OK'
    elif answer_dict['response'] == 400:
        logger.error(f'Server answer to presence message: {answer_dict["response"]}')
        return '400 Bad Request'
    else:
        logger.error(f'Server answer to presence message: {answer_dict["response"]}')
        return 'Произошла неизвестная ошибка'


def read_from_socket(sock):

    while True:
        try:
            data = get_data(sock)
            if 'response' in data and data['response'] == 404:
                raise UserDoesNotExist
            print(f"{data['time']} - {data['from']} : {data['message']}")
        except UserDoesNotExist as e:
            print(e)
            break


def write_to_socket(sock, name):
    """
    Запускается и ждет команды:
    /pm - переход в режим личных сообщений,
    /room - переход в режим общего чата,
    /exit - выход
    :param sock:
    :param name:
    :return:
    """
    while True:
        msg = input('')
        if msg == '/exit':
            break
        try:
            if msg == '/pm':
                to_whom = input('Введите имя того, кому хотите написать:\n')
                while True:
                    pm_msg = input('Сообщение: ')
                    if pm_msg == '/exit':
                        break
                    dict_msg = generate_common_chat_message(pm_msg, name, to_whom)
                    send_data(sock, dict_msg)

            if msg == '/room':
                while True:
                    r_msg = input('')
                    if r_msg == '/exit':
                        break
                    dict_msg = generate_common_chat_message(r_msg, name)
                    send_data(sock, dict_msg)

        except Exception as e:
            print(e)


def main():

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

    address = (server_address, server_port)
    user_name = input('Введите ваше имя:\n')

    transport_socket = socket(AF_INET, SOCK_STREAM)
    transport_socket.connect(address)

    # Создание потоков начинается после того, как сервер одобрил подключение, пока он всегда одобряет правильный запрос,
    # но потом возможно будет аутентификация или система банов
    server_answer = get_server_invitation(transport_socket, user_name)
    if server_answer == '200 OK':
        read_thread = Thread(target=read_from_socket, args=(transport_socket, ))
        read_thread.daemon = True
        read_thread.start()

        write_thread = Thread(target=write_to_socket, args=(transport_socket, user_name))
        write_thread.daemon = True
        write_thread.start()
    else:
        logger.error(server_answer)
        sys.exit(1)

    while True:
        time.sleep(1)
        if read_thread.is_alive():
            continue
        break


if __name__ == '__main__':
    main()

