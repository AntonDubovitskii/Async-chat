import binascii
import hmac
import os
import sys

import select
import logging
import time
import socket
import threading

from json import JSONDecodeError
from common.data_transfer import get_data, send_data, generate_auth_service_msg
from common.descriptors import Port
from common.metaclasses import ServerVerifier
from server.server_db import ServerStorage

logger = logging.getLogger('server')


class ServerMsgProc(threading.Thread):
    """
    Основной класс сервера. Принимает соединения, словари - пакеты от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    """
    port = Port("port")

    def __init__(self, listen_ipaddress, listen_port, database):
        self.addr = listen_ipaddress
        self.port = listen_port
        self.database = database
        self.sock = None
        self.clients_temp = []
        self.clients_registered = {}
        self.running = True
        super().__init__()

    @classmethod
    def generate_presence_answer(cls, data: dict):
        """Метод, генерирующий словарь-ответ на корректное presence-сообщение от клиента."""
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 200,
            "time": time.time(),
            "alert": f"Привет {data['user']['account_name']}!"
        }
        return msg

    @classmethod
    def generate_name_taken_error_msg(cls, data: dict):
        """
        Метод, генерирующий словарь-ответ,
        информирующий о возникновении ошибки с кодом 409 - имя пользователя занято.
        """
        if not isinstance(data, dict):
            raise ValueError
        msg = {
            "response": 409,
            "time": time.time(),
            "error": "Ошибка 409! Имя пользователя уже занято!"
        }
        return msg

    @classmethod
    def generate_200_ok_answer(cls):
        """Метод, генерирующий общее сообщение с кодом 200."""
        msg = {
            "response": 200,
            "time": time.time(),
            "info": ''
        }
        return msg

    @classmethod
    def generate_contact_list_answer(cls, name, db: ServerStorage):
        """Метод, генерирующий ответ на запрос списка контактов."""
        msg = {
            "response": 202,
            "time": time.time(),
            "info": db.get_contacts(name)
        }
        return msg

    @classmethod
    def generate_known_users_answer(cls, db: ServerStorage):
        """Метод, генерирующий ответ на запрос списка известных пользователей."""
        msg = {
            "response": 202,
            "time": time.time(),
            "info": [user[0] for user in db.users_list()]
        }
        return msg

    @classmethod
    def generate_invalid_request_error_msg(cls):
        """Метод, генерирующий общее сообщение об ошибке с кодом 400."""
        msg = {
            "response": 400,
            "time": time.time(),
            "error": f"Ошибка 400! Запрос некорректен!"
        }
        return msg

    @classmethod
    def generate_no_user_error_msg(cls, data: dict):
        """Метод, генерирующий сообщение об ошибке
        404 - указанный пользователь не зарегистрирован."""
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
        """Метод, генерирующий сообщение об ошибке
        410 - пользователь не в сети."""
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
        Метод, выполняющий проверку типа сообщения, принятого сервером.
        """
        if not isinstance(data, dict):
            raise ValueError

        if 'action' in data and 'time' in data and 'user' in data \
                and data['action'] == 'presence' and data['user']['account_name']:
            msg_type = 'presense_msg'
        elif 'action' in data and 'time' in data and 'from' in data \
                and 'to' in data and 'message' in data and data['action'] == 'msg' \
                and data['to'] == '#':
            msg_type = 'common_chat_msg'
        elif 'action' in data and 'time' in data and 'from' in data \
                and 'to' in data and 'message' in data \
                and data['action'] == 'msg' and data['to'] != '#':
            msg_type = 'p2p_chat_msg'
        elif 'action' in data and 'user' in data and data['action'] == 'get_contacts':
            msg_type = 'request_contacts_msg'
        elif 'action' in data and 'user' in data and 'invited_user' in data \
                and data['action'] == 'add_contact':
            msg_type = 'add_contact_msg'
        elif 'action' in data and 'user' in data and 'invited_user' in data \
                and data['action'] == 'delete_contact':
            msg_type = 'delete_contact_msg'
        elif 'action' in data and 'account' in data and data['action'] == 'users_request':
            msg_type = 'known_users_request_msg'
        elif 'action' in data and data['action'] == 'public_key_request' \
                and 'account_name' in data:
            msg_type = 'public_key_request_msg'
        elif 'action' in data and 'time' in data and 'account_name' \
                and 'message' and data['action'] == 'exit':
            msg_type = 'exit_msg'
        else:
            msg_type = 'incorrect message'

        return msg_type

    def read_requests(self, r_clients):
        """
        Формирует словарь, содержащий объекты сокетов в качестве ключа
        и словарь с переданными данными в качестве значения.
        """
        responses = {}

        for sock in r_clients:
            try:
                data = get_data(sock)
                responses[sock] = data
            except (JSONDecodeError, TypeError, OSError):
                self.remove_client(sock)
        return responses

    def authorize_user(self, message, sock):
        """Метод, реализующий авторизацию пользователей."""
        logger.debug(f'Start auth process for {message["user"]}')
        if message['user']['account_name'] in self.clients_registered.keys():
            response = ServerMsgProc.generate_name_taken_error_msg(message)
            response['error'] = 'Имя пользователя уже занято.'
            try:
                send_data(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            sock.close()
            self.clients_temp.remove(sock)
        elif not self.database.check_user(message['user']['account_name']):
            response = ServerMsgProc.generate_invalid_request_error_msg()
            response['error'] = 'Пользователь не зарегистрирован.'
            try:
                send_data(sock, response)
            except OSError:
                pass
            self.clients_temp.remove(sock)
            sock.close()
        else:
            auth_msg_dict = generate_auth_service_msg()
            random_str = binascii.hexlify(os.urandom(64))
            auth_msg_dict['data'] = random_str.decode('ascii')

            auth_hash = hmac.new(
                self.database.get_hash(message['user']['account_name']),random_str, 'MD5')
            digest = auth_hash.digest()

            try:
                send_data(sock, auth_msg_dict)
                answer = get_data(sock)
            except OSError:
                sock.close()
                return

            client_digest = binascii.a2b_base64(answer['data'])
            if 'response' in answer and answer['response'] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.clients_registered[message['user']['account_name']] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_data(sock, ServerMsgProc.generate_presence_answer(message))
                except OSError:
                    self.remove_client(message['user']['account_name'])

                self.database.user_login(
                    message['user']['account_name'],
                    client_ip,
                    client_port,
                    message['user']['public_key'])
            else:
                response = ServerMsgProc.generate_invalid_request_error_msg()
                response['error'] = 'Неверный пароль.'
                try:
                    send_data(sock, response)
                except OSError:
                    pass
                self.clients_temp.remove(sock)
                sock.close()

    def process_responses(self, requests, w_clients):
        """
        Метод, реализующий проход по словарю с полученными данными и
        выполняющий действия, соответствующие типу полученного сообщения.
        """
        for message_sock, message in requests.items():
            """
            Проверка типа сообщения, в зависимости от этого сервер посылает сообщение дальше, 
            всему чату, в лс, либо генерирует ответ на приветствие
            """
            if ServerMsgProc.identify_msg_type(message) == 'presense_msg':
                self.authorize_user(message, message_sock)

            elif ServerMsgProc.identify_msg_type(message) == 'p2p_chat_msg':
                try:
                    if message['to'] in self.clients_registered:
                        send_data(self.clients_registered[message['to']], message)
                        self.database.process_message(message['from'], message['to'])
                    else:
                        send_data(message_sock,
                                  ServerMsgProc.generate_no_user_error_msg(message))
                except (ConnectionAbortedError,ConnectionError,
                        ConnectionResetError, ConnectionRefusedError):
                    logger.info(f'Связь с клиентом {message["to"]} была потеряна')
                    self.database.user_logout(message["to"])
                    del self.clients_registered[message["to"]]
                    message_sock.close()
                    self.clients_temp.remove(message_sock)

            elif ServerMsgProc.identify_msg_type(message) == 'common_chat_msg':
                for sock in w_clients:
                    try:
                        send_data(sock, message)
                    except:
                        sock.close()
                        self.clients_temp.remove(sock)

            elif ServerMsgProc.identify_msg_type(message) == 'request_contacts_msg':
                if self.clients_registered[message['user']] == message_sock:
                    response = ServerMsgProc.generate_contact_list_answer(message['user'],
                                                                          self.database)
                    send_data(message_sock, response)
                else:
                    send_data(message_sock, ServerMsgProc.generate_invalid_request_error_msg())

            elif ServerMsgProc.identify_msg_type(message) == 'add_contact_msg':
                if self.clients_registered[message['user']] == message_sock:
                    self.database.add_contact(message['user'], message['invited_user'])
                    send_data(message_sock, ServerMsgProc.generate_200_ok_answer())
                else:
                    send_data(message_sock, ServerMsgProc.generate_invalid_request_error_msg())

            elif ServerMsgProc.identify_msg_type(message) == 'delete_contact_msg':
                if self.clients_registered[message['user']] == message_sock:
                    self.database.remove_contacts(message['user'], message['invited_user'])
                    send_data(message_sock, ServerMsgProc.generate_200_ok_answer())
                else:
                    send_data(message_sock, ServerMsgProc.generate_invalid_request_error_msg())

            elif ServerMsgProc.identify_msg_type(message) == 'known_users_request_msg':
                if self.clients_registered[message['account']] == message_sock:
                    response = ServerMsgProc.generate_known_users_answer(self.database)
                    send_data(message_sock, response)
                else:
                    send_data(message_sock, ServerMsgProc.generate_invalid_request_error_msg())

            elif ServerMsgProc.identify_msg_type(message) == 'public_key_request_msg':
                response = generate_auth_service_msg()
                response['data'] = self.database.get_pubkey(message['account_name'])

                if response['data']:
                    try:
                        send_data(message_sock, response)
                    except OSError:
                        self.remove_client(message_sock)
                else:
                    response = self.generate_invalid_request_error_msg()
                    response['error'] = 'Нет публичного ключа для данного пользователя'
                    try:
                        send_data(message_sock, response)
                    except OSError:
                        self.remove_client(message_sock)

            elif ServerMsgProc.identify_msg_type(message) == 'exit_msg':
                self.database.user_logout(message['account_name'])
                logger.info(
                    f'Клиент {message["account_name"]} корректно отключился от сервера.')
                message_sock.close()
                self.clients_temp.remove(message_sock)
                del self.clients_registered[message["account_name"]]

            else:
                send_data(message_sock, ServerMsgProc.generate_invalid_request_error_msg())

    def remove_client(self, client):
        """
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы данных.
        """
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.clients_registered:
            if self.clients_registered[name] == client:
                self.database.user_logout(name)
                del self.clients_registered[name]
                break
        self.clients_temp.remove(client)
        client.close()

    def init_socket(self):
        """Метод, инициализирующий сокет."""
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , '
            f'адрес с которого принимаются подключения: {self.addr}.'
            f' Если адрес не указан, принимаются соединения с любых адресов.')
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.addr, self.port))
            s.settimeout(0.5)
        except OSError:
            sys.exit(1)

        self.sock = s
        self.sock.listen()

    def service_update_lists(self):
        """Метод, реализующий отправку клиентам сервисного сообщения 205."""
        response = {'response': 205, "time": time.time()}
        for client in self.clients_registered:
            try:
                send_data(self.clients_registered[client], response)
            except OSError:
                self.remove_client(self.clients_registered[client])

    def run(self):
        """Метод основной цикл потока."""
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
                    to_receive_list, to_send_list, e = \
                        select.select(self.clients_temp, self.clients_temp, [], wait)
                except:
                    pass

                requests = self.read_requests(to_receive_list)
                if requests:
                    self.process_responses(requests, to_send_list)
