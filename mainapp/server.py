import select
import logging
import sys

from socket import socket, AF_INET, SOCK_STREAM
from utils.data_transfer import get_data, send_data

logger = logging.getLogger('server')


def read_requests(r_clients, all_clients):
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


def write_responses(requests, w_clients, all_clients):
    """
    Проход по словарю с полученными данными и рассылка данных всем участникам
    :param requests:
    :param w_clients:
    :param all_clients:
    :return:
    """
    for message in requests.values():
        for sock in w_clients:
            try:
                send_data(sock, message)
            except:
                sock.close()
                all_clients.remove(sock)


def main():

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 35000

        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except ValueError:
        logger.error(f'Port {listen_port} was entered. Available ports range from 1024 to 65535')
        sys.exit(1)

    address = (listen_address, listen_port)
    clients = []

    s = socket(AF_INET, SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    s.settimeout(0.2)

    while True:
        try:
            conn, addr = s.accept()

        except OSError as e:
            pass
        else:
            logger.debug(f"Получен запрос на соединение от {str(addr)}")
            clients.append(conn)
        finally:
            wait = 1
            to_receive_list = []
            to_send_list = []
            try:
                to_receive_list, to_send_list, e = select.select(clients, clients, [], wait)
            except:
                pass

            requests = read_requests(to_receive_list, clients)
            if requests:
                write_responses(requests, to_send_list, clients)


if __name__ == '__main__':

    try:
        print('Сервер запущен')
        logger.info('Сервер запущен')
        main()
    except Exception as e:
        logger.critical(e)

