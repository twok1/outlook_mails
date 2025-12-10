# tests/test_dataclasses.py
import unittest
from datetime import datetime
from src.models.dataclasses import EmailData, CommandTrip, LetterType, FORMAT_DATE

class TestDataclasses(unittest.TestCase):
    
    def test_email_data_creation(self):
        """Тестирование создания EmailData"""
        test_date = datetime(2024, 1, 1, 10, 30, 0)
        email_data = EmailData(
            message_id="test_id",
            subject="Test Subject",
            sender="test@example.com",
            body="Test body",
            recieved_date=test_date,
            msg_class=1
        )
        
        self.assertEqual(email_data.message_id, "test_id")
        self.assertEqual(email_data.subject, "Test Subject")
        self.assertEqual(email_data.sender, "test@example.com")
        self.assertEqual(email_data.body, "Test body")
        self.assertEqual(email_data.recieved_date, test_date)
        self.assertEqual(email_data.msg_class, 1)
    
    def test_command_trip_creation(self):
        """Тестирование создания CommandTrip"""
        test_date = datetime(2024, 1, 1, 10, 30, 0)
        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 15)
        order_date = datetime(2024, 1, 5)
        
        email_data = EmailData(
            message_id="test_id",
            subject="Test Subject",
            sender="test@example.com",
            body="Test body",
            recieved_date=test_date,
            msg_class=1
        )
        
        command_trip = CommandTrip(
            email_data=email_data,
            start_date=start_date,
            end_date=end_date,
            order_date=order_date,
            order_number="123",
            location="Москва",
            purpose="Деловая встреча",
            letter_type=LetterType.NEW
        )
        
        self.assertEqual(command_trip.start_date, start_date)
        self.assertEqual(command_trip.end_date, end_date)
        self.assertEqual(command_trip.order_date, order_date)
        self.assertEqual(command_trip.order_number, "123")
        self.assertEqual(command_trip.location, "Москва")
        self.assertEqual(command_trip.purpose, "Деловая встреча")
        self.assertEqual(command_trip.letter_type, LetterType.NEW)
    
    def test_command_trip_get_subject(self):
        """Тестирование метода get_subject()"""
        email_data = EmailData(
            message_id="test_id",
            subject="Test Subject",
            sender="test@example.com",
            body="Test body",
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
        
        command_trip = CommandTrip(
            email_data=email_data,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="Приказ №123",
            location="Москва",
            purpose="Деловая встреча",
            letter_type=LetterType.NEW
        )
        
        expected_subject = "[командировка] Приказ №123 05.01.2024 10.01.2024 - 15.01.2024"
        self.assertEqual(command_trip.get_subject(), expected_subject)
    
    def test_command_trip_get_text(self):
        """Тестирование метода get_text()"""
        email_data = EmailData(
            message_id="test_id",
            subject="Test Subject",
            sender="test@example.com",
            body="Test body",
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
        
        command_trip = CommandTrip(
            email_data=email_data,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="Приказ №123",
            location="Москва",
            purpose="Деловая встреча",
            letter_type=LetterType.NEW
        )
        
        expected_text = "Деловая встреча\nМосква\n10.01.2024 - 15.01.2024\n/ Приказ №123 от 05.01.2024"
        self.assertEqual(command_trip.get_text(), expected_text)
    
    def test_letter_type_enum(self):
        """Тестирование перечисления LetterType"""
        self.assertEqual(LetterType.NEW.value, 'new')
        self.assertEqual(LetterType.UPDATE.value, 'update')
        self.assertEqual(LetterType.CANCELATION.value, 'cancelation')

if __name__ == '__main__':
    unittest.main()