import sys
import logging
import threading
import time

from json import JSONDecodeError
from PyQt5.QtCore import pyqtSignal, QObject
from socket import *
from utils.data_transfer import get_data, send_data
from utils.errors import *
from datetime import datetime
from logs import client_log_config


sys.path.append('../')

logger = logging.getLogger('client')
sock_lock = threading.Lock()


class Client(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.username = username
        self.sock = None
        self.database = database
        self.connection_init(port, ip_address)

        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')

        self.running = True

    def connection_init(self, port, ip):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.settimeout(5)

        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.sock.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Установлено соединение с сервером')

        try:
            with sock_lock:
                send_data(self.sock, self.generate_greeting())
                self.server_response_parsing(get_data(self.sock))

        except (OSError, JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        logger.info('Соединение с сервером успешно установлено.')

    def generate_greeting(self):
        """
        Формирование словаря с presence-сообщением, который далее будет переведен
        в формат json и отправлен на сервер
        """
        message = {
            "action": "presence",
            "time": time.time(),
            "type": "status",
            "user": {
                "account_name": self.username,
                "status": "I am here!"
            }
        }
        logger.debug(f'Сформировано presence сообщение для пользователя {self.username}')
        return message

    def send_message(self, to, message):
        message_dict = {
            "action": "msg",
            "time": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            "from": self.username,
            "to": to,
            "message": message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        with sock_lock:
            send_data(self.sock, message_dict)
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def transport_shutdown(self):
        self.running = False
        message = {
            "action": "exit",
            "time": time.time(),
            "account_name": self.username
        }

        with sock_lock:
            try:
                send_data(self.sock, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def server_response_parsing(self, message_dict):
        if 'response' in message_dict:
            if message_dict['response'] == 200:
                return
            elif message_dict['response'] == 400:
                raise ServerError(f'{message_dict["error"]}')
            elif message_dict['response'] == 409:
                raise ServerError(f'{message_dict["error"]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message_dict["response"]}')

        elif "action" in message_dict and message_dict["action"] == "message" and "from" in message_dict \
                and "to" in message_dict and "message" in message_dict and message_dict["to"] == self.username:

            logger.debug(f'Получено сообщение от пользователя {message_dict["from"]}:{message_dict["message"]}')

        self.database.save_message(message_dict["from"], 'in' , message_dict["message"])
        self.new_message.emit(message_dict["from"])

    def contacts_list_update(self):
        logger.debug(f'Запрос контакт листа для пользователся {self.username}')
        request = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.username
        }
        logger.debug(f'Сформирован запрос {request}')
        with sock_lock:
            send_data(self.sock, request)
            ans = get_data(self.sock)
        logger.debug(f'Получен ответ {ans}')
        if 'response' in ans and ans['response'] == 202:
            for contact in ans['info']:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            'action': 'users_request',
            'time': time.time(),
            'account': self.username
        }
        with sock_lock:
            send_data(self.sock, req)
            ans = get_data(self.sock)
        if 'response' in ans and ans['response'] == 202:
            self.database.add_users(ans['info'])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            'action': 'add_contact',
            'time': time.time(),
            'user': self.username,
            'invited_user': contact
        }
        with sock_lock:
            send_data(self.sock, req)
            self.server_response_parsing(get_data(self.sock))

    def remove_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            'action': 'delete_contact',
            'time': time.time(),
            'user': self.username,
            'invited_user': contact
        }
        with sock_lock:
            send_data(self.sock, req)
            self.server_response_parsing(get_data(self.sock))

    def run(self):
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            with sock_lock:
                try:
                    self.sock.settimeout(0.5)
                    message = get_data(self.sock)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.server_response_parsing(message)
                finally:
                    self.sock.settimeout(5)

