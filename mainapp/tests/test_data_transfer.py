import json
import unittest
import time
from mainapp.utils.data_transfer import *


class TestSocket:
    """
    Класс имитирующий сокет
    """

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):

        json_test_message = json.dumps(self.test_dict)

        self.encoded_message = json_test_message.encode('utf-8')
        self.receved_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode('utf-8')


class TestDataTransfer(unittest.TestCase):

    def setUp(self) -> None:
        """
        Создание словарей участвующих в тестах
        """
        self.test_data_ok = {
            "response": 200,
            "time": time.time(),
            "alert": "Привет Guest!!"
        }

        self.test_data_error = {
            "response": 400,
            "time": time.time(),
            "error": "Bad Request"
        }

        self.test_message_send = {"action": "presence", "time": time.time(), "type": "status",
                                  "user": {"account_name": 'RandomGuy', "status": "I am here!"}}

    def test_send_data(self):
        """
        Тест функции кодирования и отправки данных
        """
        test_socket = TestSocket(self.test_message_send)

        send_data(test_socket, self.test_message_send)

        self.assertEqual(test_socket.encoded_message, test_socket.receved_message)

        with self.assertRaises(Exception):
            send_data(test_socket, test_socket)

    def test_get_data(self):
        """
        Тест функции приёма и декодирования данных
        """
        test_sock_ok = TestSocket(self.test_data_ok)
        test_sock_err = TestSocket(self.test_data_error)

        self.assertEqual(get_data(test_sock_ok), self.test_data_ok)
        self.assertEqual(get_data(test_sock_err), self.test_data_error)


if __name__ == '__main__':
    unittest.main()
