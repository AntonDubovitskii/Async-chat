"""
Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться должен только последний
октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.
"""

from ipaddress import ip_address
from pprint import pprint

from task_9_1 import host_ping


def host_range_ping():
    addr_list = []

    start_address = input('Введите начальный адрес: ')
    last_address = input('Введите последний адрес диапазона: ')
    try:
        ip_s = ip_address(start_address)
        ip_end = ip_address(last_address)
    except ValueError:
        print('Неверный формат ip-адреса!')
        exit()
    while ip_s <= ip_end:
        addr_list.append(ip_s)
        ip_s = ip_s + 1

    return host_ping(addr_list)


if __name__ == "__main__":
    pprint(host_range_ping())

"""
Введите начальный адрес: 84.252.128.1
Введите последний адрес диапазона: 84.252.128.5
[(IPv4Address('84.252.128.1'), 'узел недоступен'),
 (IPv4Address('84.252.128.2'), 'узел недоступен'),
 (IPv4Address('84.252.128.3'), 'узел доступен'),
 (IPv4Address('84.252.128.4'), 'узел доступен'),
 (IPv4Address('84.252.128.5'), 'узел доступен')]
"""

