# tests/test_reminder_calculator.py
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from src.reminder_calculator import ReminderCalculator
from src.models.dataclasses import CommandTrip, EmailData, LetterType

class TestReminderCalculator(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.calculator = ReminderCalculator()
        
        # Мокаем RussianCalendar чтобы не зависеть от реальных данных
        self.calculator.calendar = Mock()
        
        # Базовый email для тестов
        self.base_email = EmailData(
            message_id="test_id",
            subject="Test",
            sender="test@example.com",
            body="Test body",
            recieved_date=datetime(2024, 1, 1),
            msg_class=1
        )
    
    def test_run_empty_list(self):
        """Тестирование с пустым списком командировок"""
        result = self.calculator.run([])
        self.assertEqual(len(result), 0)
    
    @patch.object(ReminderCalculator, '__init__', lambda x: None)
    def test_dates_for_remind_mocked(self):
        """Тестирование с моком RussianCalendar"""
        calculator = ReminderCalculator()
        calculator.calendar = Mock()
        
        # Настраиваем мок для возврата тестовых дат
        calculator.calendar.dates_for_remind.return_value = [
            datetime(2024, 1, 8),  # Напоминание о начале
            datetime(2024, 1, 13), # Напоминание об окончании
        ]
        
        # Тестовая командировка
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
        
        result = calculator.run([trip])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].reminder_date, datetime(2024, 1, 8))
        self.assertEqual(result[1].reminder_date, datetime(2024, 1, 13))
        
        # Проверяем что метод dates_for_remind был вызван
        calculator.calendar.dates_for_remind.assert_called_once_with(trip)
    
    def test_reminder_duplicate_dates(self):
        """Тестирование устранения дубликатов дат напоминаний"""
        calculator = ReminderCalculator()
        calculator.calendar = Mock()
        
        # Настраиваем мок для возврата дублирующихся дат
        calculator.calendar.dates_for_remind.return_value = [
            datetime(2024, 1, 8),
            datetime(2024, 1, 8),  # Дубликат
            datetime(2024, 1, 13),
            datetime(2024, 1, 13), # Дубликат
        ]
        
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
        
        result = calculator.run([trip])
        
        # Должны остаться только уникальные даты
        self.assertEqual(len(result), 2)
    
    def test_reminder_subject_and_text(self):
        """Тестирование правильности формирования subject и text"""
        calculator = ReminderCalculator()
        calculator.calendar = Mock()
        
        calculator.calendar.dates_for_remind.return_value = [
            datetime(2024, 1, 8),
        ]
        
        trip = CommandTrip(
            email_data=self.base_email,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 15),
            order_date=datetime(2024, 1, 5),
            order_number="Приказ №123",
            location="Москва",
            purpose="Деловая встреча",
            letter_type=LetterType.NEW
        )
        
        result = calculator.run([trip])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].subject, "[командировка] Приказ №123 05.01.2024 10.01.2024 - 15.01.2024")
        self.assertEqual(result[0].text, "Деловая встреча\nМосква\n10.01.2024 - 15.01.2024\n/ Приказ №123 от 05.01.2024")
    
    def test_multiple_trips(self):
        """Тестирование расчета напоминаний для нескольких командировок"""
        calculator = ReminderCalculator()
        calculator.calendar = Mock()
        
        # Настраиваем разные даты для разных командировок
        def side_effect(trip):
            if trip.location == "Москва":
                return [datetime(2024, 1, 8)]
            elif trip.location == "Санкт-Петербург":
                return [datetime(2024, 2, 8)]
            return []
        
        calculator.calendar.dates_for_remind.side_effect = side_effect
        
        trips = [
            CommandTrip(
                email_data=self.base_email,
                start_date=datetime(2024, 1, 10),
                end_date=datetime(2024, 1, 15),
                order_date=datetime(2024, 1, 5),
                order_number="123",
                location="Москва",
                purpose="Встреча 1",
                letter_type=LetterType.NEW
            ),
            CommandTrip(
                email_data=self.base_email,
                start_date=datetime(2024, 2, 10),
                end_date=datetime(2024, 2, 15),
                order_date=datetime(2024, 2, 5),
                order_number="456",
                location="Санкт-Петербург",
                purpose="Встреча 2",
                letter_type=LetterType.NEW
            )
        ]
        
        result = calculator.run(trips)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].reminder_date, datetime(2024, 1, 8))
        self.assertEqual(result[1].reminder_date, datetime(2024, 2, 8))

if __name__ == '__main__':
    unittest.main()