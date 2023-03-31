"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет», «декоратор».
Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

task_file = open('test_file.txt', 'w')
task_file.write('сетевое программирование\nсокет\nдекоратор')
task_file.close()

file_encoding = task_file.encoding
print(f'Изначальная кодировка файла: {file_encoding}\n')

with open('test_file.txt', encoding=f'{file_encoding}') as f:
    for el in f:
        utf_encode = el.encode('utf-8')
        utf_decode = utf_encode.decode('utf-8')

        print(f'Вывод строки в формате Unicode: {utf_encode}\nДекодированная из utf-8 строка: {utf_decode}')

"""
Изначальная кодировка файла: UTF-8

Вывод  формате Unicode: b'\xd1\x81\xd0\xb5\xd1\x82\xd0\xb5\xd0\xb2\xd0\xbe\xd0\xb5 \0\xbc\xd0\xb8\xd1\x80\xd0
\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5\n'
Декодированная из utf-8 строка: сетевое программирование

Вывод в формате Unicode: b'\xd1\x81\xd0\xbe\xd0\xba\xd0\xb5\xd1\x82\n'
Декодированная из utf-8 строка: сокет

Вывод в формате Unicode: b'\xd0\xb4\xd0\xb5\xd0\xba\xd0\xbe\xd1\x80\xd0\xb0\xd1\x82\xd0\xbe\xd1\x80'
Декодированная из utf-8 строка: декоратор

"""