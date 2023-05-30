import configparser
import os
import select
import logging
import sys
import time
import socket
import threading
from json import JSONDecodeError

from utils.data_transfer import get_data, send_data
from logs import server_log_config
from utils.descriptors import Port
from utils.metaclasses import ServerVerifier
from server_db import ServerStorage

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


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
    def generate_200_ok_answer(cls):
        msg = {
            "response": 200,
            "time": time.time(),
            "info": ''
        }
        return msg

    @classmethod
    def generate_contact_list_answer(cls, name, db: ServerStorage):
        msg = {
            "response": 202,
            "time": time.time(),
            "info": db.get_contacts(name)
        }
        return msg

    @classmethod
    def generate_known_users_answer(cls, db: ServerStorage):
        msg = {
            "response": 202,
            "time": time.time(),
            "info": [user[0] for user in db.users_list()]
        }
        return msg

    @classmethod
    def generate_invalid_request_error_msg(cls):
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
        elif 'action' in data and 'user' in data and data['action'] == 'get_contacts':
            msg_type = 'request_contacts_msg'
        elif 'action' in data and 'user' in data and 'invited_user' in data and data['action'] == 'add_contact':
            msg_type = 'add_contact_msg'
        elif 'action' in data and 'user' in data and 'invited_user' in data and data['action'] == 'delete_contact':
            msg_type = 'delete_contact_msg'
        elif 'action' in data and 'account' in data and data['action'] == 'users_request':
            msg_type = 'known_users_request_msg'
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
            except (JSONDecodeError, TypeError, OSError):
                logger.info(f'Клиент {sock.getpeername()} отключился от сервера.')
                for name, s in self.clients_registered.items():
                    if s == sock:
                        self.database.user_logout(name)
                        del self.clients_registered[name]
                        break
                sock.close()
                all_clients.remove(sock)

        return responses

    def process_responses(self, requests, w_clients, all_clients, clients_registered):
        """
        Проход по словарю с полученными данными выполнение дейтвий соответствующих типу полученного сообщения
        :param requests:
        :param w_clients:
        :param all_clients:
        :param clients_registered:
        :return:
        """
        global new_connection

        for message_sock, message in requests.items():
            """
            Проверка типа сообщения, в зависимости от этого сервер посылает сообщение дальше, всему чату, в лс, либо
            генерирует ответ на приветствие
            """
            match Server.identify_msg_type(message):
                case 'presense_msg':
                    if message['user']['account_name'] not in self.clients_registered.keys():
                        self.clients_registered[message['user']['account_name']] = message_sock
                        client_ip, client_port = self.conn.getpeername()
                        self.database.user_login(message['user']['account_name'], client_ip, client_port)
                        send_data(message_sock, Server.generate_presence_answer(message))
                        with conflag_lock:
                            new_connection = True
                    else:
                        send_data(message_sock, Server.generate_name_taken_error_msg(message))
                        message_sock.close()
                        all_clients.remove(message_sock)

                case 'p2p_chat_msg':
                    try:
                        if message['to'] in clients_registered:
                            send_data(clients_registered[message['to']], message)
                            send_data(message_sock, message)
                            self.database.process_message(message['from'], message['to'])
                        else:
                            send_data(message_sock, Server.generate_no_user_error_msg(message))
                    except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                        logger.info(f'Связь с клиентом {message["to"]} была потеряна')
                        self.database.user_logout(message["to"])
                        del self.clients_registered[message["to"]]
                        message_sock.close()
                        all_clients.remove(message_sock)

                case 'common_chat_msg':
                    for sock in w_clients:
                        try:
                            send_data(sock, message)
                        except:
                            sock.close()
                            all_clients.remove(sock)

                case 'request_contacts_msg':
                    if self.clients_registered[message['user']] == message_sock:
                        response = Server.generate_contact_list_answer(message['user'], self.database)
                        send_data(message_sock, response)
                    else:
                        send_data(message_sock, Server.generate_invalid_request_error_msg())

                case 'add_contact_msg':
                    if self.clients_registered[message['user']] == message_sock:
                        self.database.add_contact(message['user'], message['invited_user'])
                        send_data(message_sock, Server.generate_200_ok_answer())
                    else:
                        send_data(message_sock, Server.generate_invalid_request_error_msg())

                case 'delete_contact_msg':
                    if self.clients_registered[message['user']] == message_sock:
                        self.database.remove_contacts(message['user'], message['invited_user'])
                        send_data(message_sock, Server.generate_200_ok_answer())
                    else:
                        send_data(message_sock, Server.generate_invalid_request_error_msg())

                case 'known_users_request_msg':
                    if self.clients_registered[message['account']] == message_sock:
                        response = Server.generate_known_users_answer(self.database)
                        send_data(message_sock, response)
                    else:
                        send_data(message_sock, Server.generate_invalid_request_error_msg())

                case 'exit_msg':
                    self.database.user_logout(message['account_name'])
                    logger.info(
                        f'Клиент {message["account_name"]} корректно отключился от сервера.')
                    message_sock.close()
                    all_clients.remove(message_sock)
                    del self.clients_registered[message["account_name"]]
                    with conflag_lock:
                        new_connection = True

                case _:
                    send_data(message_sock, Server.generate_invalid_request_error_msg())

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
                    self.process_responses(requests, to_send_list, self.clients_temp, self.clients_registered)


def print_help():
    print('Поддерживаемые команды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():

    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_ipaddress, listen_port = arg_parser()

    database = ServerStorage()

    server = Server(listen_ipaddress, database)
    server.port = listen_port
    server.daemon = True
    server.start()
    if server.is_alive():
        print("Сервер запущен\n")

    # print_help()

    # while True:
    #     command = input('Введите команду: ')
    #
    #     if command == 'help':
    #         print_help()
    #
    #     elif command == 'exit':
    #         exit(1)
    #
    #     elif command == 'users':
    #         users = sorted(database.users_list())
    #         if users:
    #             for user in users:
    #                 print(f'Пользователь {user[0]}, последний вход: {user[1]}')
    #         else:
    #             print("Известных пользователей пока нет")
    #
    #     elif command == 'connected':
    #         users = sorted(database.active_users_list())
    #         if users:
    #             for user in users:
    #                 print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
    #         else:
    #             print("Нет ни одного подключенного к серверу пользователя")
    #
    #     elif command == 'loghist':
    #         name = input('Введите имя пользователя для просмотра истории. Для вывода всей истории, просто нажмите Enter: ')
    #         history = sorted(database.login_history(name))
    #         if history:
    #             for user in history:
    #                 print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
    #         else:
    #             print("Данный пользователь не зарегистрирован")
    #
    #     else:
    #         print('Команда не распознана.')

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    try:
        logger.info('Сервер запущен')
        main()
    except Exception as e:
        print("\n", e)
        logger.critical(e)

