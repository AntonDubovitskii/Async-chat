"""
Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2. Но в данном случае
результат должен быть итоговым по всем ip-адресам, представленным в табличном формате (использовать модуль tabulate).
"""

from task_9_2 import host_range_ping
from tabulate import tabulate


def host_range_tab():
    host_range = host_range_ping()
    reach_list = []
    unreach_list = []

    for addr in host_range:
        reach_list.append((addr[0], )) if addr[1] == 'узел доступен' else unreach_list.append((addr[0], ))

    print(tabulate(reach_list, headers=['Reachable'], tablefmt="pipe", stralign="center"))
    print()
    print(tabulate(unreach_list, headers=['Unreachable'], tablefmt="pipe", stralign="center"))


if __name__ == "__main__":
    host_range_tab()

"""
Введите начальный адрес: 84.252.128.1
Введите последний адрес диапазона: 84.252.128.8
|  Reachable   |
|:------------:|
| 84.252.128.3 |
| 84.252.128.4 |
| 84.252.128.5 |
| 84.252.128.8 |

|  Unreachable  |
|:-------------:|
| 84.252.128.1  |
| 84.252.128.2  |
| 84.252.128.6  |
| 84.252.128.7  |
"""

