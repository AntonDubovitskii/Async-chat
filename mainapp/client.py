import json
import sys
from socket import *
import time


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

    # Формирование словаря с presence-сообщением, который далее будет переведен
    # в формат json и отправлен на сервер
    presence_msg = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {
            "account_name": "RandomGuy",
            "status": "I am here!"
        }

    }

    objs = json.dumps(presence_msg, indent=4, ensure_ascii=False)
    s.send(objs.encode('utf-8'))
    data = s.recv(1000000).decode('utf-8')

    data_dict = json.loads(data)
    if data_dict['response'] == 200:
        print('200 OK')
    elif data_dict['response'] == 400:
        print('400 Bad Request')
    else:
        print('Произошла неизвестная ошибка')
    s.close()


if __name__ == '__main__':

    try:
        main()
    except Exception as e:
        print(e)

