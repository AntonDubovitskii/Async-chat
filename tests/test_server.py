import unittest
import time

from mainapp.server import process_presence_msg


class TestServer(unittest.TestCase):

    def setUp(self) -> None:
        self.ok_message = {
            "action": "presence",
            "time": time.time(),
            "type": "status",
            "user": {
                "account_name": 'RandomGuy',
                "status": "I am here!"
            }
        }

    def test_correct_processing(self):
        """Обработка корректного сообщения"""
        self.assertEqual(200, process_presence_msg(self.ok_message)["response"])

    def test_no_action(self):
        """Нет поля action, должен вернуться ответ с кодом 400"""
        self.assertEqual(400, process_presence_msg({"time": time.time(), "type": "status", "user":
            {"account_name": 'RandomGuy', "status": "I am here!"}})["response"])

    def test_no_time(self):
        """Нет поля time, должен вернуться ответ с кодом 400"""
        self.assertEqual(400, process_presence_msg({"action": "presence", "type": "status", "user":
            {"account_name": 'RandomGuy', "status": "I am here!"}})["response"])

    def test_no_accaunt_name(self):
        """Нет полей user и account_name, должен вернуться ответ с кодом 400"""
        self.assertEqual(400, process_presence_msg({"action": "presence", "time": time.time(), "type": "status"})[
            "response"])


if __name__ == "__main__":
    unittest.main()
