import select
import logging
import sys
import time
import socket

from utils.data_transfer import get_data, send_data
from logs import server_log_config
from utils.descriptors import Port
from utils.metaclasses import ServerVerifier

logger = logging.getLogger('server')


def arg_parser():
    if '-a' in sys.argv:
        listen_address = sys.argv[sys.argv.index('-a') + 1]
    else:
        listen_address = ''

    if '-p' in sys.argv:

        listen_port = int(sys.argv[sys.argv.index('-p') + 1])

    else:
        listen_port = 7777
    return listen_address, listen_port


class Server(metaclass=ServerVerifier):

    port = Port("port")

    def __init__(self, listen_ipaddress):
        self.addr = listen_ipaddress
        self.clients_temp = []
        # Словарь, временно имитирующий бд, где регистрируются пользователи
        self.clients_registered = {}

    @classmethod
    def generate_presence_answer(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 200,
            "time": time.time(),
            "alert": f"Привет {data['user']['account_name']}!"
        }
        return msg

    @classmethod
    def generate_no_user_error_msg(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 404,
            "time": time.time(),
            "error": f"Ошибка 404! Пользователь {data['to']} не зарегистрирован"
        }
        return msg

    @classmethod
    def generate_user_not_online_error_msg(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 410,
            "time": time.time(),
            "error": f"Ошибка 410! Пользователь {data['to']} не в сети"
        }
        return msg

    @classmethod
    def identify_msg_type(cls, data: dict):
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

    def read_requests(self, r_clients, all_clients):
        """
        Формирует словарь, содержащий объекты сокетов в качестве ключа и словарь с переданными данными
        в качестве значения
        :param r_clients:
        :param all_clients:
        :return:
        """
        responses = {}

        for sock in r_clients:
            try:
                data = get_data(sock)
                responses[sock] = data
            except:
                sock.close()
                all_clients.remove(sock)

        return responses

    def write_responses(self, requests, w_clients, all_clients, clients_registered):
        """
        Проход по словарю с полученными данными выполнение дейтвий соответствующих типу полученного сообщения
        :param requests:
        :param w_clients:
        :param all_clients:
        :param clients_registered:
        :return:
        """

        for message_sock, message in requests.items():
            """
            Проверка типа сообщения, в зависимости от этого сервер посылает сообщение дальше, всему чату, в лс, либо
            генерирует ответ на приветствие
            """
            if Server.identify_msg_type(message) == 'presense_msg':
                clients_registered[message['user']['account_name']] = message_sock
                send_data(message_sock, Server.generate_presence_answer(message))
                continue

            elif Server.identify_msg_type(message) == 'p2p_chat_msg':
                try:
                    if message['to'] in clients_registered:
                        send_data(clients_registered[message['to']], message)
                        send_data(message_sock, message)
                    else:
                        send_data(message_sock, Server.generate_no_user_error_msg(message))
                except:
                    message_sock.close()
                    all_clients.remove(message_sock)

            elif Server.identify_msg_type(message) == 'common_chat_msg':
                for sock in w_clients:
                    try:
                        send_data(sock, message)
                    except:
                        sock.close()
                        all_clients.remove(sock)

    def init_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(0.2)

        self.sock = s
        self.sock.listen()

    def main_loop(self):
        self.init_socket()
        while True:
            try:
                conn, addr = self.sock.accept()

            except OSError as e:
                pass
            else:
                logger.debug(f"Получен запрос на соединение от {str(addr)}")
                self.clients_temp.append(conn)
            finally:
                wait = 1
                to_receive_list = []
                to_send_list = []
                try:
                    to_receive_list, to_send_list, e = select.select(self.clients_temp, self.clients_temp, [], wait)
                except:
                    pass

                requests = self.read_requests(to_receive_list, self.clients_temp)
                if requests:
                    self.write_responses(requests, to_send_list, self.clients_temp, self.clients_registered)


def main():

    listen_ipaddress, listen_port = arg_parser()
    server = Server(listen_ipaddress)
    server.port = listen_port
    server.main_loop()


if __name__ == '__main__':
    try:
        print('Сервер запущен')
        logger.info('Сервер запущен')
        main()
    except Exception as e:
        print(e)
        logger.critical(e)

