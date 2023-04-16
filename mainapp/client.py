import sys
import time
from socket import *
from mainapp.data_transfer import get_data, send_data


def generate_greeting(account_name='Guest'):
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


def process_server_answer(data_dict):
    """
    Обработка ответа от сервера на presence-сообщение
    """
    if data_dict['response'] == 200:
        return '200 OK'
    elif data_dict['response'] == 400:
        return '400 Bad Request'
    else:
        return 'Произошла неизвестная ошибка'


def main():

    # Проверка и парсинг параметров командной строки
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 1111
    except ValueError:
        print('Ошибка! Доступные порты находятся в диапазоне от 1024 до 65535.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_address, server_port))

    presence_msg = generate_greeting('Anton_1993')
    send_data(s, presence_msg)

    data_dict = get_data(s)
    process_server_answer(data_dict)

    s.close()


if __name__ == '__main__':

    try:
        main()
    except Exception as e:
        print(e)

