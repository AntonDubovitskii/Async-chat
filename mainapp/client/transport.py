import binascii
import hashlib
import hmac
import sys
import logging
import threading
import time

from json import JSONDecodeError
from PyQt5.QtCore import pyqtSignal, QObject
from socket import *
from utils.data_transfer import get_data, send_data, generate_auth_service_msg
from utils.errors import *
from datetime import datetime
from logs import client_log_config


sys.path.append('../')

logger = logging.getLogger('client')
sock_lock = threading.Lock()


class Client(threading.Thread, QObject):
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.username = username
        self.password = passwd
        self.keys = keys
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

        password_encoded = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha256', password_encoded, salt, 100000)
        password_hex = binascii.hexlify(passwd_hash)

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with sock_lock:
            presense = self.generate_greeting(pubkey)
            logger.debug(f"Presense message = {presense}")

            try:
                send_data(self.sock, presense)
                answer = get_data(self.sock)
                logger.debug(f'Server response = {answer}.')

                if 'response' in answer:
                    if answer['response'] == 400:
                        raise ServerError(answer['error'])
                    elif answer['response'] == 511:
                        ans_data = answer['data']
                        hash = hmac.new(password_hex, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = generate_auth_service_msg()
                        my_ans['data'] = binascii.b2a_base64(digest).decode('ascii')
                        send_data(self.sock, my_ans)
                        self.server_response_parsing(get_data(self.sock))

            except (OSError, JSONDecodeError):
                logger.critical('Потеряно соединение с сервером!')
                raise ServerError('Потеряно соединение с сервером!')

            logger.info('Соединение с сервером успешно установлено.')

    def generate_greeting(self, pubkey):
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
                "public_key": pubkey
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
            elif message_dict['response'] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message_dict["response"]}')

        elif "action" in message_dict and message_dict["action"] == "msg" and "from" in message_dict \
                and "to" in message_dict and "message" in message_dict and message_dict["to"] == self.username:

            logger.debug(f'Получено сообщение от пользователя {message_dict["from"]}:{message_dict["message"]}')

            self.new_message.emit(message_dict)

    def contacts_list_update(self):
        self.database.contacts_clear()
        logger.debug(f'Запрос контакт листа для пользователя {self.username}')
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

    def key_request(self, user):
        logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            'action': 'public_key_request',
            'time': time.time(),
            'account_name': user
        }
        with sock_lock:
            send_data(self.sock, req)
            ans = get_data(self.sock)
        if 'response' in ans and ans['response'] == 511:
            return ans['data']
        else:
            logger.error(f'Не удалось получить ключ собеседника{user}.')

    def run(self):
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            message = None
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
                finally:
                    self.sock.settimeout(5)

            if message:
                logger.debug(f'Принято сообщение с сервера: {message}')
                self.server_response_parsing(message)

