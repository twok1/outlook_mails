# tests/test_command_trip_processor.py
import unittest
from datetime import datetime
from src.command_trip_processor import CommandTripProcessor
from src.models.dataclasses import CommandTrip, EmailData, LetterType

class TestCommandTripProcessor(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.processor = CommandTripProcessor()
        
        # Базовый email для тестов
        self.base_email = EmailData(
            message_id="test_id",
            subject="Test",
            sender="test@example.com",
            body="Test body",
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
    
    def test_process_single_new_trip(self):
        """Тестирование обработки одной новой командировки"""
        trip = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Встреча",
            letter_type=LetterType.NEW
        )
        
        result = self.processor.run([trip])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].location, "Москва")
        self.assertEqual(result[0].letter_type, LetterType.NEW)
    
    def test_process_update_existing_trip(self):
        """Тестирование обновления существующей командировки"""
        # Создаем новую командировку
        new_trip = CommandTrip(
            email_data=EmailData(
                message_id="id1",
                subject="Test1",
                sender="test@example.com",
                body="Body1",
                recieved_date=datetime(2024, 1, 1),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Первоначальная цель",
            letter_type=LetterType.NEW
        )
        
        # Создаем обновление для той же командировки
        update_trip = CommandTrip(
            email_data=EmailData(
                message_id="id2",
                subject="Test2",
                sender="test@example.com",
                body="Body2",
                recieved_date=datetime(2024, 1, 2),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 12),
            end_date=datetime(2024, 1, 17),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Обновленная цель",
            letter_type=LetterType.UPDATE
        )
        
        result = self.processor.run([new_trip, update_trip])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].start_date, datetime(2024, 1, 12))
        self.assertEqual(result[0].end_date, datetime(2024, 1, 17))
        self.assertEqual(result[0].purpose, "Обновленная цель")
    
    def test_process_different_locations(self):
        """Тестирование обработки командировок в разных локациях"""
        trip1 = CommandTrip(
            email_data=EmailData(
                message_id="id1",
                subject="Test1",
                sender="test@example.com",
                body="Body1",
                recieved_date=datetime(2024, 1, 1),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 1",
            letter_type=LetterType.NEW
        )
        
        trip2 = CommandTrip(
            email_data=EmailData(
                message_id="id2",
                subject="Test2",
                sender="test@example.com",
                body="Body2",
                recieved_date=datetime(2024, 1, 2),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 20),
            end_date=datetime(2024, 1, 25),
            order_date=datetime(2024, 1, 15),
            order_number="456",
            location="Санкт-Петербург",
            purpose="Цель 2",
            letter_type=LetterType.NEW
        )
        
        result = self.processor.run([trip1, trip2])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].location, "Москва")
        self.assertEqual(result[1].location, "Санкт-Петербург")
    
    def test_is_one_trip_same_location_overlapping_dates(self):
        """Тестирование определения одной командировки с пересекающимися датами"""
        trip1 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 1",
            letter_type=LetterType.NEW
        )
        
        trip2 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 12),
            end_date=datetime(2024, 1, 17),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 2",
            letter_type=LetterType.UPDATE
        )
        
        self.assertTrue(self.processor._is_one_trip(trip2, trip1))
    
    def test_is_one_trip_different_locations(self):
        """Тестирование определения разных командировок по локациям"""
        trip1 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 1",
            letter_type=LetterType.NEW
        )
        
        trip2 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Санкт-Петербург",
            purpose="Цель 2",
            letter_type=LetterType.UPDATE
        )
        
        self.assertFalse(self.processor._is_one_trip(trip2, trip1))
    
    def test_is_one_trip_non_overlapping_dates(self):
        """Тестирование определения разных командировок по непересекающимся датам"""
        trip1 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 1",
            letter_type=LetterType.NEW
        )
        
        trip2 = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 2, 10),
            end_date=datetime(2024, 2, 15),
            order_date=datetime(2024, 2, 5),
            order_number="456",
            location="Москва",
            purpose="Цель 2",
            letter_type=LetterType.UPDATE
        )
        
        self.assertFalse(self.processor._is_one_trip(trip2, trip1))
    
    def test_sorting_by_received_date(self):
        """Тестирование сортировки по дате получения"""
        trip1 = CommandTrip(
            email_data=EmailData(
                message_id="id1",
                subject="Test1",
                sender="test@example.com",
                body="Body1",
                recieved_date=datetime(2024, 1, 3),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="123",
            location="Москва",
            purpose="Цель 1",
            letter_type=LetterType.NEW
        )
        
        trip2 = CommandTrip(
            email_data=EmailData(
                message_id="id2",
                subject="Test2",
                sender="test@example.com",
                body="Body2",
                recieved_date=datetime(2024, 1, 1),
                msg_class=1
            ),
            start_date=datetime(2024, 1, 20),
            end_date=datetime(2024, 1, 25),
            order_date=datetime(2024, 1, 15),
            order_number="456",
            location="Санкт-Петербург",
            purpose="Цель 2",
            letter_type=LetterType.NEW
        )
        
        # trip2 должен быть первым, так как получен раньше
        result = self.processor.run([trip1, trip2])
        self.assertEqual(result[0].email_data.recieved_date, datetime(2024, 1, 1))
        self.assertEqual(result[1].email_data.recieved_date, datetime(2024, 1, 3))

if __name__ == '__main__':
    unittest.main()