"""
2. Задание на закрепление знаний по модулю json. Есть файл orders
в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий
его заполнение данными.

Для этого:
Создать функцию write_order_to_json(), в которую передается
5 параметров — товар (item), количество (quantity), цена (price),
покупатель (buyer), дата (date). Функция должна предусматривать запись
данных в виде словаря в файл orders.json. При записи данных указать
величину отступа в 4 пробельных символа;

Проверить работу программы через вызов функции write_order_to_json()
с передачей в нее значений каждого параметра.
"""
import json
from datetime import datetime


def write_order_to_json(item, quantity, price, buyer, date=datetime.now()):
    date_str = f'{date.strftime("%d/%m/%Y %H:%M:%S")}'
    temp_dict = {'item': item, 'quantity': quantity, 'price': price, 'buyer': buyer, 'date': date_str}

    with open('orders.json', encoding='utf-8') as f:
        f_content = f.read()
        objs = json.loads(f_content)

    with open('orders.json', 'w', encoding='utf-8') as f:
        objs['orders'].append(temp_dict)
        json.dump(objs, f, indent=4, ensure_ascii=False)


write_order_to_json('TV r10-lef', 1, 65078, 'Иванов И.А.')
write_order_to_json('Printer f12A', 20, 10233, 'Сидоров Г.У.')
write_order_to_json('Scaner tr10', 1, 8300, 'Еремина Д.Н.')

