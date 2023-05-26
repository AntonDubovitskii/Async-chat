import select
import logging
import sys
import time
import socket
import threading

from utils.data_transfer import get_data, send_data
from logs import server_log_config
from utils.descriptors import Port
from utils.metaclasses import ServerVerifier
from server_db import ServerStorage

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


class Server(threading.Thread, metaclass=ServerVerifier):

    port = Port("port")

    def __init__(self, listen_ipaddress, database):
        self.addr = listen_ipaddress
        self.database = database
        self.clients_temp = []
        self.clients_registered = {}

        super().__init__()

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
    def generate_name_taken_error_msg(cls, data:dict):
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 409,
            "time": time.time(),
            # "error": f"Ошибка 409! Имя пользователя {data['from']} уже занято!"
            "error": "Ошибка 409! Имя пользователя уже занято!"
        }
        return msg

    @classmethod
    def generate_invalid_request_error_msg(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 400,
            "time": time.time(),
            "error": f"Ошибка 400! Запрос некорректен!"
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
        elif 'action' in data and 'time' in data and 'account_name' and 'message' and data['action'] == 'exit':
            msg_type = 'exit_msg'
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
                if message['user']['account_name'] not in self.clients_registered.keys():
                    self.clients_registered[message['user']['account_name']] = message_sock
                    client_ip, client_port = self.conn.getpeername()
                    self.database.user_login(message['user']['account_name'], client_ip, client_port)
                    send_data(message_sock, Server.generate_presence_answer(message))
                else:
                    send_data(message_sock, Server.generate_name_taken_error_msg(message))
                    message_sock.close()
                    all_clients.remove(message_sock)

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

            elif Server.identify_msg_type(message) == 'exit_msg':
                self.database.user_logout(message['account_name'])
                message_sock.close()
                all_clients.remove(message_sock)

            else:
                send_data(message_sock, Server.generate_invalid_request_error_msg(message))

    def init_socket(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.addr, self.port))
            s.settimeout(0.2)
        except OSError:
            exit(1)

        self.sock = s
        self.sock.listen()

    def run(self):
        self.init_socket()

        while True:
            try:
                self.conn, self.addr = self.sock.accept()

            except OSError as e:
                pass
            else:
                logger.debug(f"Получен запрос на соединение от {str(self.addr)}")
                self.clients_temp.append(self.conn)
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


def print_help():
    print('Поддерживаемые команды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():

    listen_ipaddress, listen_port = arg_parser()

    database = ServerStorage()

    server = Server(listen_ipaddress, database)
    server.port = listen_port
    server.daemon = True
    server.start()

    print_help()

    while True:
        command = input('Введите команду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            exit(1)
        elif command == 'users':
            for user in sorted(database.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.active_users_list()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input('Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    try:
        logger.info('Сервер запущен')
        main()
    except Exception as e:
        print(e)
        logger.critical(e)

