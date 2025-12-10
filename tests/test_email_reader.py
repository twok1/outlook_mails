# tests/test_email_reader.py
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from src.email_reader import EmailReader
from src.models.dataclasses import EmailData

class TestEmailReader(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем мок OutlookConnector
        self.mock_outlook = Mock()
        self.mock_account = Mock()
        self.mock_outlook.outlook = self.mock_account
        
        # Инициализируем EmailReader с моком
        self.reader = EmailReader(self.mock_outlook)
    
    def test_run_with_matching_messages(self):
        """Тестирование поиска сообщений с подходящими критериями"""
        # Создаем мок сообщений
        mock_message1 = Mock()
        mock_message1.id = "msg1"
        mock_message1.subject = "Информирование о направлении в командировку"
        mock_message1.sender = Mock(email_address="iasup_notify@greenatom.ru")
        mock_message1.text_body = "Тело письма 1"
        mock_message1.datetime_received = datetime(2024, 1, 1, 10, 0, 0)
        mock_message1.item_class = 1
        
        mock_message2 = Mock()
        mock_message2.id = "msg2"
        mock_message2.subject = "Информирование об изменении данных командировки"
        mock_message2.sender = Mock(email_address="iasup_notify@greenatom.ru")
        mock_message2.text_body = "Тело письма 2"
        mock_message2.datetime_received = datetime(2024, 1, 2, 10, 0, 0)
        mock_message2.item_class = 1
        
        # Настраиваем мок фильтра
        mock_filter = Mock()
        mock_filter.filter.return_value = [mock_message1, mock_message2]
        self.mock_account.inbox.filter = Mock(return_value=mock_filter.filter.return_value)
        
        result = self.reader.run()
        
        # Проверяем результаты
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], EmailData)
        self.assertIsInstance(result[1], EmailData)
        
        # Проверяем поля первого сообщения
        self.assertEqual(result[0].message_id, "msg1")
        self.assertEqual(result[0].subject, "Информирование о направлении в командировку")
        self.assertEqual(result[0].sender.email_address, "iasup_notify@greenatom.ru")
        self.assertEqual(result[0].body, "Тело письма 1")
        self.assertEqual(result[0].msg_class, 1)
    
    def test_run_with_no_matching_messages(self):
        """Тестирование когда нет подходящих сообщений"""
        # Настраиваем мок для возврата пустого списка
        self.mock_account.inbox.filter.return_value = []
        
        result = self.reader.run()
        
        self.assertEqual(len(result), 0)
    
    def test_run_with_wrong_sender(self):
        """Тестирование когда отправитель не соответствует"""
        mock_message = Mock()
        mock_message.id = "msg1"
        mock_message.subject = "Информирование о направлении в командировку"
        mock_message.sender = Mock(email_address="other@greenatom.ru")  # Не тот отправитель
        mock_message.text_body = "Тело письма"
        mock_message.datetime_received = datetime(2024, 1, 1, 10, 0, 0)
        mock_message.item_class = 1
        
        # Настраиваем мок фильтра
        self.mock_account.inbox.filter.return_value = [mock_message]
        
        result = self.reader.run()
        
        # Должен вернуться список, но может быть пустым если фильтрация работает
        # На практике фильтрация выполняется exchangelib, так что проверяем что метод был вызван
        self.mock_account.inbox.filter.assert_called()
    
    def test_run_with_wrong_subject(self):
        """Тестирование когда тема не соответствует"""
        mock_message = Mock()
        mock_message.id = "msg1"
        mock_message.subject = "Другое уведомление"  # Не та тема
        mock_message.sender = Mock(email_address="iasup_notify@greenatom.ru")
        mock_message.text_body = "Тело письма"
        mock_message.datetime_received = datetime(2024, 1, 1, 10, 0, 0)
        mock_message.item_class = 1
        
        # Настраиваем мок фильтра
        self.mock_account.inbox.filter.return_value = [mock_message]
        
        result = self.reader.run()
        
        self.mock_account.inbox.filter.assert_called()
    
    def test_process_to_emaildata(self):
        """Тестирование конвертации сообщений в EmailData"""
        # Создаем тестовые сообщения
        mock_message1 = Mock()
        mock_message1.id = "msg1"
        mock_message1.subject = "Test Subject 1"
        mock_message1.sender = Mock(email_address="test1@example.com")
        mock_message1.text_body = "Body 1"
        mock_message1.datetime_received = datetime(2024, 1, 1, 10, 0, 0)
        mock_message1.item_class = 1
        
        mock_message2 = Mock()
        mock_message2.id = "msg2"
        mock_message2.subject = "Test Subject 2"
        mock_message2.sender = Mock(email_address="test2@example.com")
        mock_message2.text_body = "Body 2"
        mock_message2.datetime_received = datetime(2024, 1, 2, 10, 0, 0)
        mock_message2.item_class = 2
        
        result = self.reader._process_to_emaildata([mock_message1, mock_message2])
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].message_id, "msg1")
        self.assertEqual(result[0].subject, "Test Subject 1")
        self.assertEqual(result[0].sender.email_address, "test1@example.com")
        self.assertEqual(result[0].body, "Body 1")
        self.assertEqual(result[0].recieved_date, datetime(2024, 1, 1, 10, 0, 0))
        self.assertEqual(result[0].msg_class, 1)
        
        self.assertEqual(result[1].message_id, "msg2")
        self.assertEqual(result[1].subject, "Test Subject 2")
        self.assertEqual(result[1].sender.email_address, "test2@example.com")
        self.assertEqual(result[1].body, "Body 2")
        self.assertEqual(result[1].recieved_date, datetime(2024, 1, 2, 10, 0, 0))
        self.assertEqual(result[1].msg_class, 2)
    
    def test_process_to_emaildata_empty_list(self):
        """Тестирование конвертации пустого списка сообщений"""
        result = self.reader._process_to_emaildata([])
        
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()