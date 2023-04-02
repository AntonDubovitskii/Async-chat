"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе.
"""


def check_encode_error(words: list):
    for word in words:
        try:
            print(bytes(word, 'ascii'))
        except UnicodeEncodeError:
            print(f'Слово "{word}" невозможно записать в виде байтовой строки')


first_word = 'attribute'
second_word = 'класс'
third_word = 'функция'
fourth_word = 'type'

word_list = [first_word, second_word, third_word, fourth_word]

check_encode_error(word_list)

"""
b'attribute'
Слово "класс" невозможно записать в виде байтовой строки
Слово "функция" невозможно записать в виде байтовой строки
b'type'

Вывод: для записи слова в виде байтовой строки могут использоваться только стандартные символы ASCII. Второе и 
третье слова записаны кириллицей, что приводит к ошибке.
"""
