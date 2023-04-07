"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt,
info_3.txt и формирующий новый «отчетный» файл в формате CSV.

Для этого:

Создать функцию get_data(), в которой в цикле осуществляется перебор файлов
с данными, их открытие и считывание данных. В этой функции из считанных данных
необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения каждого параметра поместить в соответствующий список. Должно
получиться четыре списка — например, os_prod_list, os_name_list,
os_code_list, os_type_list. В этой же функции создать главный список
для хранения данных отчета — например, main_data — и поместить в него
названия столбцов отчета в виде списка: «Изготовитель системы»,
«Название ОС», «Код продукта», «Тип системы». Значения для этих
столбцов также оформить в виде списка и поместить в файл main_data
(также для каждого файла);

Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(),
а также сохранение подготовленных данных в соответствующий CSV-файл;

Проверить работу программы через вызов функции write_to_csv().
"""

import csv
import re
from chardet.universaldetector import UniversalDetector


def get_data():

    # Проверяем какая кодировка использовалась в переданных нам файлах
    detector = UniversalDetector()
    with open('info_1.txt', 'rb') as test_file:
        for i in test_file:
            detector.feed(i)
            if detector.done:
                break
        detector.close()

    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = []

    file_number = 0

    # На случай если файлов больше трёх, перебираем пока не поймаем ошибку
    try:
        while True:
            file_number += 1
            file_obj = open(f'info_{file_number}.txt', encoding=detector.result['encoding'])
            data = file_obj.read()

            # Заполнение списка изготовителей системы
            os_prod_reg = re.search(r'(Изготовитель системы:)([^\n\r]*)', data)
            os_prod_list.append(os_prod_reg.group(2).strip())

            # Заполнение списка названий ОС
            os_name_reg = re.search(r'(Название ОС:)([^\n\r]*)', data)
            os_name_list.append(os_name_reg.group(2).strip())

            # Заполнение списка кодов продуктов
            os_code_reg = re.search(r'(Код продукта:)([^\n\r]*)', data)
            os_code_list.append(os_code_reg.group(2).strip())

            # Заполнение списка типов систем
            os_type_reg = re.search(r'(Тип системы:)([^\n\r]*)', data)
            os_type_list.append(os_type_reg.group(2).strip())
    except FileNotFoundError:
        files_count = file_number

    headers = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    main_data.append(headers)

    for i in range(0, files_count-1):
        row_data = [os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]]
        main_data.append(row_data)
    return main_data


def write_to_csv(file):

    main_data = get_data()
    with open(file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        for row in main_data:
            writer.writerow(row)


write_to_csv('data_report.csv')

