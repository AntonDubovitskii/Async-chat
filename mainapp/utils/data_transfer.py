import json


def get_data(soc, length=100000, encoding='utf-8'):

    data = soc.recv(length)

    if isinstance(data, bytes):
        decoded_data = data.decode(encoding)
        data_dict = json.loads(decoded_data)
        if isinstance(data_dict, dict):
            return data_dict
        raise ValueError
    raise ValueError


def send_data(soc, data: dict):
    """
    Преобразование переданного словаря в json формат, кодирование в utf-8 и отправка на сервер
    """
    if not isinstance(data, dict):
        raise ValueError
    objs = json.dumps(data)
    encoded_objs = objs.encode('utf-8')
    soc.send(encoded_objs)






