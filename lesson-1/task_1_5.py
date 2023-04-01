"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового
в строковый тип на кириллице.
"""
import subprocess

import chardet

args = ['ping', 'yandex.ru']

yandex_ping = subprocess.Popen(args, stdout=subprocess.PIPE)

for line in yandex_ping.stdout:
    result = chardet.detect(line)
    line = line.decode('cp866').encode('utf-8').decode('utf-8')
    print(line)

"""
Отдельный пинг youtube.com наверное нет смысла делать, это идентичный код.
"""