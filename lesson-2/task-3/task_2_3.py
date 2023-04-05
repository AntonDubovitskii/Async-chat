"""
3. Задание на закрепление знаний по модулю yaml.
Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата.

Для этого:

Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим в кодировке
ASCII(например, €);

Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла с помощью
параметра default_flow_style, а также установить возможность работы
с юникодом: allow_unicode = True;

Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""

import yaml

data = {'car_models': ['BMW X6 M Competition 2024', 'BMW 5 Series Hybrid 2023', 'BMW M240i 2023'],
        'manufacturer_id:': 172893,
        'prices': {'BMW X6 M Competition 2024': '117.024€', 'BMW 5 Series Hybrid 2023': '51.888€',
                   'BMW M240i 2023': '44.068€'}
        }

with open('file.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

with open('file.yaml', encoding='utf-8') as f:
    f_content = yaml.load(f, Loader=yaml.SafeLoader)

print(f_content)

