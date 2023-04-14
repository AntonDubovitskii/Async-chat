import unittest
from mainapp.client import process_server_answer, generate_greeting


class TestClient(unittest.TestCase):

    def test_generate_greeting(self):
        """Тест на корректность сгенерированного словаря.
        Так как само сообщение пока не в окончательном виде, тест со временем придется исправлять"""
        greeting = generate_greeting()
        greeting['time'] = 1.234  # Использована константа, так как одинаковое время получить нельзя

        self.assertEqual(greeting, {"action": "presence", "time": 1.234, "type": "status",
                                    "user": {"account_name": 'Guest', "status": "I am here!"}})

    def test_process_server_answer_200(self):
        """Проверка ответа сервера при отсутствии ошибки, должен вернуться код 200 OK"""
        self.assertEqual(process_server_answer({"response": 200}), '200 OK')

    def test_process_server_answer_400(self):
        """Проверка ответа сервера при некорректном запросе, должен вернуться код 400 Bad Request"""
        self.assertEqual(process_server_answer({"response": 400}), '400 Bad Request')

    def test_process_server_answer_not_200_or_400(self):
        """Проверка ответа сервера при возникновении ошибки отличной от некорректного запроса.
        Не должен выдавать коды 200K или 400 Bad Request"""
        self.assertNotIn(process_server_answer({"response": '500'}), ('200 OK', '400 Bad Request'))


if __name__ == "__main__":
    unittest.main()

