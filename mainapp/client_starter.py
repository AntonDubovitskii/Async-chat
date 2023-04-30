import sys

from utils.client_utils import *
from client_read_only import *
from client_write_only import *

logger = logging.getLogger('client')


def client():

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
    client_mode = input('Введите режим работы клинта: r - режим приема сообщений, w - режим отправки сообщений\n')

    if client_mode == 'r':
        create_read_mode_socket(address)

    elif client_mode == 'w':
        create_write_mode_socket(address, user_name)

    else:
        print("Введена некорретная команда!")


if __name__ == '__main__':

    try:
        client()
    except Exception as e:
        logger.critical(e)

