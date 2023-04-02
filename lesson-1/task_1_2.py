"""
2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность кодов
(не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.
"""


def check_words(words: list):
    for word in words:
        print(word, type(word), 'длина: ', len(word))


first_word_bytes = b'class'
second_word_bytes = b'function'
third_word_bytes = b'method'

word_list = [first_word_bytes, second_word_bytes, third_word_bytes]

check_words(word_list)

"""
b'class' <class 'bytes'> длина:  5
b'function' <class 'bytes'> длина:  8
b'method' <class 'bytes'> длина:  6
"""

