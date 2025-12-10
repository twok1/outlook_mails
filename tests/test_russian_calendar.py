# tests/test_russian_calendar.py
import unittest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.russian_calendar import RussianCalendar

class TestRussianCalendar(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем тестовые данные
        self.test_holidays = {
            "2024": [
                {"month": 0, "day": 1, "name": "Новый год"},
                {"month": 0, "day": 2, "name": "Новый год"},
            ]
        }
        
        self.test_short_days = {
            "2024": [
                {"month": 1, "day": 22, "name": "День защитника Отечества"},
            ]
        }
        
        self.test_working_holidays = {
            "2024": [
                {"month": 11, "day": 28, "name": "Новый год"},
            ]
        }
    
    @patch('src.russian_calendar.requests.get')
    @patch('src.russian_calendar.Path')
    def test_load_calendar_file_exists(self, mock_path, mock_get):
        """Тестирование загрузки календаря когда файл существует"""
        # Мокаем путь и открытие файла
        mock_file = mock_open(read_data=json.dumps(self.test_holidays))
        
        calendar = RussianCalendar()
        
        # Проверяем что requests.get не вызывался
        mock_get.assert_not_called()
    
    @patch('src.russian_calendar.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.russian_calendar.Path.exists')
    def test_load_calendar_file_not_exists(self, mock_exists, mock_open_func, mock_get):
        """Тестирование загрузки календаря когда файл не существует"""
        # Файл не существует
        mock_exists.return_value = False
        
        # Мокаем ответ от сервера
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = self.test_holidays
        mock_get.return_value = mock_response
        
        calendar = RussianCalendar()
        
        # Проверяем что requests.get был вызван
        mock_get.assert_called()
        
        # Проверяем что файл был записан
        mock_open_func.assert_called()
    
    def test_date_eq_line(self):
        """Тестирование сравнения даты с записью календаря"""
        calendar = RussianCalendar()
        
        test_date = datetime(2024, 1, 1)  # 1 января 2024
        test_line = {"month": 0, "day": 1, "name": "Новый год"}  # Месяц 0 = январь
        
        self.assertTrue(calendar._date_eq_line(test_date, test_line))
        
        # Неправильная дата
        test_date2 = datetime(2024, 2, 1)
        self.assertFalse(calendar._date_eq_line(test_date2, test_line))
    
    @patch('src.russian_calendar.RussianCalendar._download_calendars')
    def test_is_working_day_holiday(self, mock_download):
        """Тестирование проверки выходного дня"""
        # Настраиваем мок с тестовыми данными
        calendar = RussianCalendar()
        calendar.holidays = self.test_holidays
        calendar.short_days = self.test_short_days
        calendar.working_holidays = self.test_working_holidays
        
        # 1 января - выходной
        holiday_date = datetime(2024, 1, 1)
        self.assertFalse(calendar.is_working_day(holiday_date))
        
        # 3 января - рабочий день (не в списке праздников)
        work_date = datetime(2024, 1, 3)
        self.assertTrue(calendar.is_working_day(work_date))
    
    @patch('src.russian_calendar.RussianCalendar._download_calendars')
    def test_is_working_day_weekend(self, mock_download):
        """Тестирование проверки выходных (суббота/воскресенье)"""
        calendar = RussianCalendar()
        calendar.holidays = {"2024": []}
        calendar.short_days = {"2024": []}
        calendar.working_holidays = {"2024": []}
        
        # Суббота
        saturday = datetime(2024, 1, 6)  # 6 января 2024 - суббота
        self.assertFalse(calendar.is_working_day(saturday))
        
        # Воскресенье
        sunday = datetime(2024, 1, 7)  # 7 января 2024 - воскресенье
        self.assertFalse(calendar.is_working_day(sunday))
        
        # Понедельник
        monday = datetime(2024, 1, 8)  # 8 января 2024 - понедельник
        self.assertTrue(calendar.is_working_day(monday))
    
    @patch('src.russian_calendar.RussianCalendar._download_calendars')
    def test_is_working_day_short_day(self, mock_download):
        """Тестирование проверки сокращенного дня"""
        calendar = RussianCalendar()
        calendar.holidays = {"2024": []}
        calendar.short_days = self.test_short_days
        calendar.working_holidays = {"2024": []}
        
        # 23 февраля - сокращенный день
        short_day = datetime(2024, 2, 23)
        self.assertTrue(calendar.is_working_day(short_day))
    
    @patch('src.russian_calendar.RussianCalendar._download_calendars')
    def test_is_working_day_working_holiday(self, mock_download):
        """Тестирование проверки рабочего праздничного дня"""
        calendar = RussianCalendar()
        calendar.holidays = {"2024": []}
        calendar.short_days = {"2024": []}
        calendar.working_holidays = self.test_working_holidays
        
        # 29 декабря - рабочий праздничный день
        working_holiday = datetime(2024, 12, 29)
        self.assertTrue(calendar.is_working_day(working_holiday))
    
    @patch('src.russian_calendar.RussianCalendar._download_calendars')
    def test_dates_for_remind(self, mock_download):
        """Тестирование расчета дат для напоминаний"""
        calendar = RussianCalendar()
        
        # Мокаем is_working_day для тестов
        calendar.is_working_day = Mock(return_value=True)
        
        # Создаем мок командировки
        mock_trip = Mock()
        mock_trip.start_date = datetime(2024, 1, 10)  # Среда
        mock_trip.end_date = datetime(2024, 1, 15)    # Понедельник
        
        # START_NOTIFICATION = [-7, -3, -1]
        # END_NOTIFICATION = [-1]
        # Предполагаем конфигурацию по умолчанию
        
        result = calendar.dates_for_remind(mock_trip)
        
        # Проверяем что метод был вызван для расчетных дат
        self.assertTrue(calendar.is_working_day.called)

if __name__ == '__main__':
    unittest.main()