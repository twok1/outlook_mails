from copy import copy
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.command_trip_processor import CommandTripProcessor, CommandTrip
from src.models.dataclasses import EmailData, LetterType

class TestCommandTripProcessor:
    @pytest.fixture(autouse=True)
    def setup_command_trip_processor(self):
        self.processor = CommandTripProcessor()
        
    def test_is_one_trip(self):
        trip1 = CommandTrip(
            Mock(spec=EmailData),
            datetime(2025, 1, 1),
            datetime(2025, 1, 5),
            datetime(2025, 1, 1),
            '1',
            'Moscow',
            'target',
            LetterType.NEW
        )
        trip2 = copy(trip1)
        trip2.end_date = datetime(2025, 1, 10)
        assert self.processor._is_one_trip(trip1, trip2)
        
        trip2.start_date = datetime(2024, 12, 20)
        trip2.end_date = datetime(2025, 1, 5)
        assert self.processor._is_one_trip(trip1, trip2)
        
        trip2.start_date = datetime(2025, 1, 6)
        trip2.end_date = datetime(2025, 1, 10)
        assert not self.processor._is_one_trip(trip1, trip2)
        
        trip3 = copy(trip1)
        trip3.location = 'Rostov'
        assert not self.processor._is_one_trip(trip1, trip3)
        

    def test_run_all_new(self):
        email_data = Mock(spec=EmailData)
        test_data = []
        for i in range(3):
            com = Mock(spec=CommandTrip)
            email_data.recieved_date = datetime(2025, 1, 1 + i)
            com.email_data = email_data
            com.letter_type = LetterType.NEW
            test_data.append(com)
                
        self.processor._is_one_trip = Mock(return_value=False)
        
        result = self.processor.run(test_data)
        
        assert len(result) == len(test_data)
        assert result == test_data
        
    def test_run_all_new_sorting(self):
        test_data = []
        for i in range(3):
            com = Mock(spec=CommandTrip)
            email_data = Mock(spec=EmailData)
            email_data.recieved_date = datetime(2025, 1, 15 - i)
            com.email_data = email_data
            com.letter_type = LetterType.NEW
            test_data.append(com)
                
        self.processor._is_one_trip = Mock(return_value=False)
        
        result = self.processor.run(test_data)
        
        assert result == test_data[::-1]