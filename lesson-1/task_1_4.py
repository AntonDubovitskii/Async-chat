"""
4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое
и выполнить обратное преобразование (используя методы encode и decode).
"""


def encode_list(words: list):
    for index, word in enumerate(words):
        words[index] = word.encode('utf-8')
        print(words[index], type(words[index]))


def decode_list(words: list):
    for index, word in enumerate(words):
        words[index] = word.decode('utf-8')
        print(words[index], type(words[index]))


first_word = 'разработка'
second_word = 'администрирование'
third_word = 'protocol'
fourth_word = 'standard'

word_list = [first_word, second_word, third_word, fourth_word]

encode_list(word_list)

print('-' * 30)

decode_list(word_list)


