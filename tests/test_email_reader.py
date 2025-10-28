from copy import copy
from datetime import datetime
from typing import List
from unittest.mock import Mock, patch
import pytest

from src.email_reader import EmailReader
from src.models.dataclasses import EmailData


@pytest.fixture
def mock_outlook():
    with patch('src.email_reader.win32com.client.Dispatch') as mock_dispatch:
        mock_app = Mock()
        mock_namespace = Mock()
        mock_folder = Mock()
        
        mock_dispatch.return_value = mock_app
        mock_app.GetNamespace.return_value = mock_namespace
        mock_namespace.GetDefaultFolder.return_value = mock_folder
        
        yield mock_dispatch, mock_app, mock_namespace, mock_folder
    

class TestEmailReader:
    def test_init_email_reader(self, mock_outlook):
        mock_dispatch, mock_app, _, _ = mock_outlook
        
        reader = EmailReader()
        
        mock_dispatch.assert_called_once_with("Outlook.Application")
        mock_app.GetNamespace.assert_called_once_with("MAPI")
        assert(reader.OUTLOOK_INBOX == 6)
        assert(reader.OUTLOOK_INBOX == reader.folder)
        assert (isinstance(reader.outlook, Mock))
        
    def test_run(self, mock_outlook):
        _, _, _, mock_folder = mock_outlook
        mock_folder.Items = self._create_outlook_mock_emails()
        
        reader = EmailReader()
        
        assert(len(reader.run()) == 2)
        
    @staticmethod
    def _create_outlook_mock_emails() -> list:
        result = []
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование о направлении в командировку',
            SenderEmailAddress='iasup_notify@greenatom.ru',
            Class=54
        ))
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование об изменении данных командировки',
            SenderEmailAddress='iasup_notify@greenatom.ru',
            Class=54
        ))
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование о направлении в командировку1',
            SenderEmailAddress='iasup_notify@greenatom.ru',
            Class=54
        ))
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование об изменении данных командировки1',
            SenderEmailAddress='iasup_notify@greenatom.ru',
            Class=54
        ))
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование о направлении в командировку',
            SenderEmailAddress='iasup_notify1@greenatom.ru',
            Class=54
        ))
        
        result.append(TestEmailReader._create_mock_email(
            Subject='Информирование о направлении в командировку',
            SenderEmailAddress='iasup_notify@greenatom.ru',
            Class=52
        ))
        
        return result
    
    @staticmethod
    def _create_mock_email(**kwargs):
        defaults = {
            'EntryID': '1', 
            'Subject': 'ERROR',
            'SenderEmailAddress': 'nobody@rosatom.ru',
            'Body': 'str',
            'ReceivedTime': datetime.now(),
            'Class': 52
        }
        email = Mock()
        for kw in (defaults, kwargs):
            for key, val in kw.items():
                setattr(email, key, val)
        return email