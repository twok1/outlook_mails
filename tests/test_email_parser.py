# tests/test_email_parser.py
import unittest
from datetime import datetime
from src.email_parser import EmailParser
from src.models.dataclasses import EmailData, LetterType

class TestEmailParser(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.parser = EmailParser()
        
        # Тестовый email для новой командировки
        self.new_command_email_body = """Уважаемый сотрудник!
        
Вы направлены в командировку с 10.01.2024 по 15.01.2024, приказ от 01.01.2024 № 01-01-2024-1/К.
В: Москва.
С целью - Деловая встреча с партнерами
Дополнительная информация: ..."""
        
        # Тестовый email для обновления командировки
        self.update_command_email_body = """Уважаемый сотрудник!
        
Условия указанной командировки изменены. Ознакомьтесь, пожалуйста, с новыми условиями.
Вы направлены в командировку с 12.01.2024 по 17.01.2024, приказ от 01.01.2024 № 01-01-2024-1/К.
В: Санкт-Петербург.
С целью - Презентация проекта
Дополнительная информация: ..."""
        
    def test_parse_new_command_trip(self):
        """Тестирование парсинга нового уведомления о командировке"""
        email_data = EmailData(
            message_id="test_id",
            subject="Информирование о направлении в командировку",
            sender="iasup_notify@greenatom.ru",
            body=self.new_command_email_body,
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
        
        result = self.parser.parse(email_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.start_date, datetime(2024, 1, 10))
        self.assertEqual(result.end_date, datetime(2024, 1, 15))
        self.assertEqual(result.order_date, datetime(2024, 1, 1))
        self.assertEqual(result.order_number, "01-01-2024-1/К")
        self.assertEqual(result.location, "Москва")
        self.assertEqual(result.purpose, "Деловая встреча с партнерами")
        self.assertEqual(result.letter_type, LetterType.NEW)
    
    def test_parse_update_command_trip(self):
        """Тестирование парсинга обновления командировки"""
        email_data = EmailData(
            message_id="test_id",
            subject="Информирование об изменении данных командировки",
            sender="iasup_notify@greenatom.ru",
            body=self.update_command_email_body,
            recieved_date=datetime(2024, 1, 6),
            msg_class=1
        )
        
        result = self.parser.parse(email_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.start_date, datetime(2024, 1, 12))
        self.assertEqual(result.end_date, datetime(2024, 1, 17))
        self.assertEqual(result.order_date, datetime(2024, 1, 1))
        self.assertEqual(result.order_number, "01-01-2024-1/К")
        self.assertEqual(result.location, "Санкт-Петербург")
        self.assertEqual(result.purpose, "Презентация проекта")
        self.assertEqual(result.letter_type, LetterType.UPDATE)
    
    def test_parse_multiple_emails(self):
        """Тестирование парсинга нескольких писем"""
        emails = [
            EmailData(
                message_id="test1",
                subject="Информирование о направлении в командировку",
                sender="iasup_notify@greenatom.ru",
                body=self.new_command_email_body,
                recieved_date=datetime(2024, 1, 1),
                msg_class=1
            ),
            EmailData(
                message_id="test2",
                subject="Информирование об изменении данных командировки",
                sender="iasup_notify@greenatom.ru",
                body=self.update_command_email_body,
                recieved_date=datetime(2024, 1, 6),
                msg_class=1
            )
        ]
        
        results = self.parser.run(emails)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].letter_type, LetterType.NEW)
        self.assertEqual(results[1].letter_type, LetterType.UPDATE)
    
    def test_parse_invalid_email(self):
        """Тестирование парсинга некорректного письма"""
        invalid_email_body = "Некорректное тело письма без необходимых данных"
        
        email_data = EmailData(
            message_id="test_id",
            subject="Некорректный email",
            sender="test@example.com",
            body=invalid_email_body,
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
        
        with self.assertRaises(ValueError):
            self.parser.parse(email_data)
    
    def test_parse_order_number_without_dot(self):
        """Тестирование парсинга номера приказа без точки в конце"""
        email_body = """Вы направлены в командировку с 10.01.2024 по 15.01.2024, приказ от 01.01.2024 № 01-01-2024-1/К"""
        
        email_data = EmailData(
            message_id="test_id",
            subject="Test",
            sender="test@example.com",
            body=email_body,
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
        
        # Должен вернуть None, так как нет точки после номера приказа
        order_number = self.parser._parse_order_number(
            "Вы направлены в командировку с 10.01.2024 по 15.01.2024, приказ от 01.01.2024 № 01-01-2024-1/К"
        )
        self.assertIsNone(order_number)

if __name__ == '__main__':
    unittest.main()