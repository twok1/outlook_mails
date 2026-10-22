# tests/conftest.py
import pytest
import sys
import os

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Фикстуры для тестов
@pytest.fixture
def sample_email_data():
    """Фикстура с тестовыми данными EmailData"""
    from datetime import datetime
    from src.models.dataclasses import EmailData
    
    return EmailData(
        message_id="test_id",
        subject="Test Subject",
        sender="test@example.com",
        body="Test body",
        received_date=datetime(2024, 1, 1, 10, 0, 0),
        msg_type=1
    )

@pytest.fixture
def sample_command_trip():
    """Фикстура с тестовыми данными CommandTrip"""
    from datetime import datetime
    from src.models.dataclasses import CommandTrip, EmailData, LetterType
    
    email_data = EmailData(
        message_id="test_id",
        subject="Test Subject",
        sender="test@example.com",
        body="Test body",
        received_date=datetime(2024, 1, 1, 10, 0, 0),
        msg_type=1
    )
    
    return CommandTrip(
        email_data=email_data,
        start_date=datetime(2024, 1, 10),
        end_date=datetime(2024, 1, 15),
        order_date=datetime(2024, 1, 5),
        order_number="123",
        location="Москва",
        purpose="Встреча",
        letter_type=LetterType.NEW
    )

@pytest.fixture
def email_parser():
    """Фикстура для EmailParser"""
    from src.parsers.trip_mail_parser import TripEmailParser
    return TripEmailParser()

@pytest.fixture
def command_trip_processor():
    """Фикстура для CommandTripProcessor"""
    from src.processors.trip_processor import CommandTripProcessor
    return CommandTripProcessor()