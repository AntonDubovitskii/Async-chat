import argparse
import os
import sys
import logging

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication
from utils.errors import *
from client.client_db import ClientDatabase
from client.transport import Client
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from logs import client_log_config

logger = logging.getLogger('client')


def arg_parser():
    """Парсер аргументов коммандной строки."""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default='7777', type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    address = namespace.addr
    port = namespace.port
    name = namespace.name
    password = namespace.password

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return address, port, name, password


if __name__ == '__main__':
    server_address, server_port, client_name, client_passwd = arg_parser()

    client_app = QApplication(sys.argv)

    start_dialog = UserNameDialog()

    if not client_name or not client_passwd:
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    database = ClientDatabase(client_name)

    try:
        transport = Client(server_port, server_address, database, client_name, client_passwd, keys)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.daemon = True
    transport.start()

    del start_dialog

    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
