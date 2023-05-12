"""
Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""
import subprocess
import socket

from ipaddress import ip_address
from pprint import pprint


def host_ping(list_ip_addresses: list):

    result_list = []
    for address in list_ip_addresses:
        # Сохранение адреса в изначальном виде, чтобы пользователю было удобнее
        host_name = address
        try:
            ip_address_obj = ip_address(address)
        except ValueError:
            # Если пользователь ввел не ip адрес, а домен, его следует привести к стандартному виду
            try:
                ip_address_obj = ip_address(socket.gethostbyname(address))
            except socket.error:
                print(f"Ошибка в адресе {host_name}")
                continue

        proc = subprocess.Popen(f"ping {ip_address_obj} -w 1", shell=True, stdout=subprocess.PIPE)

        proc.wait()
        # Метод .returncode вернет 0, если дочерний процесс завершился успешно
        host_state = f'{"узел доступен" if proc.returncode == 0 else "узел недоступен"}'

        result_list.append((host_name, host_state))
    return result_list


if __name__ == "__main__":
    ip_addresses = ["google.com", "ya.ru", "instagram.com", "8.8.8.8"]
    pprint(host_ping(ip_addresses))

"""
google.com - узел доступен
ya.ru - узел доступен
instagram.com - узел недоступен
8.8.8.8 - узел доступен
"""

