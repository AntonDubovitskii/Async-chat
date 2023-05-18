import sys
import logging
import time

from socket import *
from threading import Thread
from utils.data_transfer import get_data, send_data
from utils.errors import *
from datetime import datetime

from utils.metaclasses import ClientVerifier

logger = logging.getLogger('client')


class Client(metaclass=ClientVerifier):

    def __init__(self, username, sock):
        self.username = username
        self.sock = sock

    @classmethod
    def arg_parser(cls):
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
        return server_address, server_port

    @classmethod
    def get_server_invitation(cls, sock, username):
        """
        Выполняет процедуру обмена приветствиями с сервером
        :param sock:
        :param username:
        :return:
        """
        greeting = Client.generate_greeting(username)
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

    @classmethod
    def generate_greeting(cls, account_name='Guest'):
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

    @classmethod
    def generate_common_chat_message(cls, message, account_name='Guest', destination='#', current_datetime=None):
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

    def read_from_socket(self, sock):

        while True:
            try:
                data = get_data(sock)
                if 'response' in data and data['response'] == 404:
                    raise UserDoesNotExist
                print(f"{data['time']} - {data['from']} : {data['message']}")
            except UserDoesNotExist as e:
                print(e)
                break

    def write_to_socket(self, sock, name):
        """
        Запускается и ждет команды:
        /pm - переход в режим личных сообщений,
        /room - переход в режим общего чата,
        /exit - выход
        :param sock:
        :param name:
        :return:
        """
        print('Введите одну из команд: /exit - для выхода, /pm - для перехода в режим личных сообщений, '
              '/room - для перехода в режим общего чата')
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
                        dict_msg = Client.generate_common_chat_message(pm_msg, name, to_whom)
                        send_data(sock, dict_msg)

                if msg == '/room':
                    while True:
                        r_msg = input('')
                        if r_msg == '/exit':
                            break
                        dict_msg = Client.generate_common_chat_message(r_msg, name)
                        send_data(sock, dict_msg)

            except Exception as e:
                print(e)


def main():

    address = (Client.arg_parser())
    user_name = input('Введите ваше имя:\n')

    transport_socket = socket(AF_INET, SOCK_STREAM)
    transport_socket.connect(address)

    # Создание потоков начинается после того, как сервер одобрил подключение, пока он всегда одобряет правильный запрос,
    # но потом возможно будет аутентификация или система банов
    server_answer = Client.get_server_invitation(transport_socket, user_name)
    if server_answer == '200 OK':
        client_obj = Client(user_name, transport_socket)

        read_thread = Thread(target=client_obj.read_from_socket, args=(client_obj.sock, ))
        read_thread.daemon = True
        read_thread.start()

        write_thread = Thread(target=client_obj.write_to_socket, args=(client_obj.sock, client_obj.username))
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

