import sys
import logging
import threading
import time
from json import JSONDecodeError

from socket import *
from threading import Thread
from utils.data_transfer import get_data, send_data
from utils.errors import *
from datetime import datetime

from utils.metaclasses import ClientVerifier
from client_db import ClientDatabase

logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class Client(metaclass=ClientVerifier):

    def __init__(self, username, sock, database):
        self.username = username
        self.sock = sock
        self.database = database

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
        elif answer_dict['response'] == 409:
            logger.error(f'Server answer to presence message: {answer_dict["response"]}')
            return answer_dict['error']
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

    @classmethod
    def generate_exit_message(cls, account_name):
        """
        Формирование словаря с exit-сообщением, который далее будет переведен
        в формат json и отправлен на сервер
        """
        message = {
            "action": "exit",
            "time": time.time(),
            "account_name": account_name,
        }
        return message

    def chat_info(self):
        print('\nВведите одну из команд: \n/exit - для выхода, \n/pm - для перехода в режим личных сообщений, '
              '\n/chat_room - для перехода в режим общего чата, \n/history - вывод истории сообщений,'
              '\n/contacts - вывод списка контактов, \n/edit - редактирование контактов.')

    def read_from_socket(self, sock):
        try:
            while True:
                time.sleep(1)
                with sock_lock:
                    try:
                        data = get_data(sock)
                        if 'response' in data and int(data['response']) in (400, 404, 410):
                            raise ServerError(data['error'])

                        elif 'info' in data:
                            print(data['info'])

                        else:
                            print(f"{data['time']} - {data['from']} : {data['message']}")
                    except ServerError as e:
                        print(e)
                        break
        except JSONDecodeError:
            exit(1)

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
        self.chat_info()
        while True:
            msg = input('')
            if msg == '/exit':
                dict_msg = Client.generate_exit_message(name)
                try:
                    send_data(sock, dict_msg)
                except:
                    pass
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                exit(1)
            try:
                if msg == '/pm':
                    to_whom = input('Введите имя того, кому хотите написать:\n')

                    with database_lock:
                        if not self.database.check_user(to_whom):
                            logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_whom}')
                            exit(1)

                    print(f"Личный чат с пользователем {to_whom}: \n")
                    while True:
                        pm_msg = input('Сообщение: ')
                        if pm_msg == '/exit':
                            self.chat_info()
                            break
                        dict_msg = Client.generate_common_chat_message(pm_msg, name, to_whom)

                        # Сохранение сообщения в историю
                        with database_lock:
                            self.database.save_message(name, to_whom, pm_msg)
                        send_data(sock, dict_msg)

                if msg == '/chat_room':
                    print(f"Общий чат: \n")
                    while True:
                        r_msg = input('')
                        if r_msg == '/exit':
                            self.chat_info()
                            break
                        dict_msg = Client.generate_common_chat_message(r_msg, name)
                        send_data(sock, dict_msg)

                if msg == '/contacts':
                    with database_lock:
                        contacts_list = self.database.get_contacts()
                    for contact in contacts_list:
                        print(contact)
                    self.chat_info()

                if msg == '/edit':
                    self.edit_contacts()
                    self.chat_info()

                if msg == '/history':
                    self.print_history()
                    self.chat_info()

            except OSError as err:
                if err.errno:
                    logger.critical('Потеряно соединение с сервером.')
                else:
                    logger.error('Не удалось передать сообщение. Таймаут соединения')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                try:
                    add_contact(self.sock, self.username, edit)
                except ServerError as err:
                    print(err)
                    logger.error('Не удалось отправить информацию на сервер.')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.username)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.username)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(
                        f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от '
                        f'{message[3]}\n{message[2]}')


def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        'action': 'users_request',
        'time': time.time(),
        'account': username
    }
    send_data(sock, req)
    ans = get_data(sock)
    if "response" in ans and ans["response"] == 202:
        return ans["info"]
    else:
        raise ServerError


def contacts_list_request(sock, username):
    logger.debug(f'Запрос контакт листа для пользователся {username}')
    request = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': username
    }
    logger.debug(f'Сформирован запрос {request}')
    send_data(sock, request)
    answer = get_data(sock)
    logger.debug(f'Получен ответ {answer}')
    if "response" in answer and answer["response"] == 202:
        return answer["info"]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'invited_user': contact
    }
    send_data(sock, req)
    ans = get_data(sock)
    print(ans)
    if "response" in ans and ans["response"] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'delete_contact',
        'time': time.time(),
        'user': username,
        'invited_user': contact
    }
    send_data(sock, req)
    ans = get_data(sock)
    if "response" in ans and ans["response"] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


def database_load(sock, db, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        db.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            db.add_contact(contact)


def main():

    address = (Client.arg_parser())
    user_name = input('Введите ваше имя:\n')

    transport_socket = socket(AF_INET, SOCK_STREAM)
    transport_socket.connect(address)

    # Создание потоков и бд начинается после того, как сервер одобрил подключение
    server_answer = Client.get_server_invitation(transport_socket, user_name)
    if server_answer == '200 OK':
        database = ClientDatabase(user_name)
        database_load(transport_socket, database, user_name)

        client_obj = Client(user_name, transport_socket, database)

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

