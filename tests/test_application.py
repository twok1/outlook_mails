# tests/test_application.py
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.application import Application
from src.models.dataclasses import CommandTrip, EmailData, LetterType, Reminder

class TestApplication(unittest.TestCase):
    
    @patch('src.application.OutlookConnector')
    @patch('src.application.EmailReader')
    @patch('src.application.EmailParser')
    @patch('src.application.CommandTripProcessor')
    @patch('src.application.ReminderCalculator')
    @patch('src.application.ReminderManager')
    def test_run_integration(self, mock_reminder_manager, mock_reminder_calculator, 
                            mock_command_trip_processor, mock_email_parser, 
                            mock_email_reader, mock_outlook_connector):
        """Интеграционный тест всего процесса"""
        # Настраиваем моки
        mock_outlook = Mock()
        mock_outlook_connector.return_value = mock_outlook
        
        # Настраиваем EmailReader
        mock_reader_instance = Mock()
        mock_email_reader.return_value = mock_reader_instance
        mock_reader_instance.run.return_value = [
            EmailData(
                message_id="msg1",
                subject="Информирование о направлении в командировку",
                sender="iasup_notify@greenatom.ru",
                body="Тестовое тело",
                recieved_date=datetime(2024, 1, 1),
                msg_class=1
            )
        ]
        
        # Настраиваем EmailParser
        mock_parser_instance = Mock()
        mock_email_parser.return_value = mock_parser_instance
        mock_parser_instance.run.return_value = [
            CommandTrip(
                email_data=EmailData(
                    message_id="msg1",
                    subject="Test",
                    sender="test@example.com",
                    body="Test body",
                    recieved_date=datetime(2024, 1, 1),
                    msg_class=1
                ),
                start_date=datetime(2024, 1, 10),
                end_date=datetime(2024, 1, 15),
                order_date=datetime(2024, 1, 5),
                order_number="123",
                location="Москва",
                purpose="Встреча",
                letter_type=LetterType.NEW
            )
        ]
        
        # Настраиваем CommandTripProcessor
        mock_processor_instance = Mock()
        mock_command_trip_processor.return_value = mock_processor_instance
        mock_processor_instance.run.return_value = [
            CommandTrip(
                email_data=EmailData(
                    message_id="msg1",
                    subject="Test",
                    sender="test@example.com",
                    body="Test body",
                    recieved_date=datetime(2024, 1, 1),
                    msg_class=1
                ),
                start_date=datetime(2024, 1, 10),
                end_date=datetime(2024, 1, 15),
                order_date=datetime(2024, 1, 5),
                order_number="123",
                location="Москва",
                purpose="Встреча",
                letter_type=LetterType.NEW
            )
        ]
        
        # Настраиваем ReminderCalculator
        mock_calculator_instance = Mock()
        mock_reminder_calculator.return_value = mock_calculator_instance
        mock_calculator_instance.run.return_value = [
            Reminder(
                reminder_date=datetime(2024, 1, 8),
                subject="[командировка] 123 05.01.2024 10.01.2024 - 15.01.2024",
                text="Встреча\nМосква\n10.01.2024 - 15.01.2024\n/ 123 от 05.01.2024"
            )
        ]
        
        # Настраиваем ReminderManager
        mock_manager_instance = Mock()
        mock_reminder_manager.return_value = mock_manager_instance
        
        # Создаем и запускаем приложение
        app = Application()
        app.run()
        
        # Проверяем что все методы были вызваны в правильном порядке
        mock_outlook_connector.assert_called_once()
        mock_email_reader.assert_called_once_with(outlook=mock_outlook)
        mock_reader_instance.run.assert_called_once()
        mock_email_parser.assert_called_once()
        mock_parser_instance.run.assert_called_once()
        mock_command_trip_processor.assert_called_once()
        mock_processor_instance.run.assert_called_once()
        mock_reminder_calculator.assert_called_once()
        mock_calculator_instance.run.assert_called_once()
        mock_reminder_manager.assert_called_once_with(outlook=mock_outlook)
        mock_manager_instance.run.assert_called_once()
    
    @patch('src.application.OutlookConnector')
    def test_init(self, mock_outlook_connector):
        """Тестирование инициализации Application"""
        mock_outlook = Mock()
        mock_outlook_connector.return_value = mock_outlook
        
        app = Application()
        
        # Проверяем что все компоненты были созданы
        self.assertIsNotNone(app.mail_reader)
        self.assertIsNotNone(app.mail_parser)
        self.assertIsNotNone(app.command_trip_processor)
        self.assertIsNotNone(app.remind_calculator)
        self.assertIsNotNone(app.remind_manager)
        
        # Проверяем что OutlookConnector был создан
        mock_outlook_connector.assert_called_once()

if __name__ == '__main__':
    unittest.main()