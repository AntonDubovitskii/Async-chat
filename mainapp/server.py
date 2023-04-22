import sys
import time
import logging


sys.path.append("..")

from logs import server_log_config
from socket import *
from mainapp.data_transfer import get_data, send_data
from additional_tools.log_decorator import log

logger = logging.getLogger('server')


@log
def process_presence_msg(data: dict):
    """
    Проверка обязательных полей json объекта, необходимых для соответствия протоколу JIM
    и формирование соответствующего словаря для ответа клиенту
    """
    if 'action' in data and 'time' in data and 'user' in data \
            and data['action'] == 'presence' and data['user']['account_name']:
        msg = {
            "response": 200,
            "time": time.time(),
            "alert": f"Привет {data['user']['account_name']}!"
        }
    else:
        msg = {
            "response": 400,
            "time": time.time(),
            "error": "Bad Request"
        }
    return msg


def main():

    # Проверка и парсинг параметров командной строки
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

    # Инициализация сокета на основании полученных параметров
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((listen_address, listen_port))
    s.listen(5)

    while True:
        client, addr = s.accept()
        data = get_data(client)

        logger.info(f'{data["action"]} message was sent by the client: {addr}'.capitalize())

        answer_msg = process_presence_msg(data)

        try:
            send_data(client, answer_msg)
            logger.info(f'Response with a code {answer_msg["response"]} was sent to the client: {addr}')
        except ValueError as e:
            logger.error(e)

        client.close()


if __name__ == '__main__':

    try:
        main()
    except Exception as e:
        logger.critical(e)

