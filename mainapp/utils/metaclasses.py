import dis


class ServerMeta(type):
    """
    Метакласс для проверки соответствия сервера
    """

    def __init__(self, clsname, bases, clsdict):

        methods = []
        attrs = []

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])

            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы и атрибуты.
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        print(methods)
        # При обнаружении недопустимого метода вызывается исключение
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        # В случае если сокет не инициализирован константами SOCK_STREAM(TCP) AF_INET(IPv4), вызывается исключение
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, bases, clsdict)


class ClientMeta(type):
    """
    Метакласс для проверки корректности клиентов
    """

    def __init__(self, clsname, bases, clsdict):

        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция - необходимо обработать исключение
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        # Если обнаружено использование недопустимого метода accept, listen, socket бросаем исключение:
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        # Признаком корректной работы с сокетом является вызов утилит отправки и приема данных
        if 'get_data' in methods or 'send_data' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(clsname, bases, clsdict)

