Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

Скрипт decorators.py
---------------------

.. automodule:: common.decorators
    :members:

Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.Port
    :members:

Скрипт errors.py
---------------------

.. autoclass:: common.errors.ServerError
   :members:

Скрипт metaclasses.py
-----------------------

.. autoclass:: common.metaclasses.ServerVerifier
   :members:

.. autoclass:: common.metaclasses.ClientVerifier
   :members:

Скрипт data_transfer.py
------------------------

common.data_transfer. **get_data** (soc, length=100000, encoding='utf-8')


    Получение данных с указанного сокета, проведение декодирования и преобразование в формат словаря.

common.data_transfer. **send_data** (sock, data: dict)


    Преобразование переданного словаря в json формат, кодирование в utf-8
    и отправка на сервер.

