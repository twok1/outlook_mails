from datetime import datetime
import pytest
from unittest.mock import Mock, patch

from src.email_parser import EmailParser, LetterType
from src.models.dataclasses import CommandTrip, EmailData

class TestEmailParser:
    TEST_ORDER_DATE = '31.12.2024'
    TEST_ORDER_NUMBER = '31-12-2024-1/К'
    TEST_START_DATE = '01.01.2025'
    TEST_END_DATE = '31.12.2025'
    TEST_LOCATION = 'Российская Федерация'
    TEST_PURPOSE = 'Выполнение тестирования'
    CHANGED_COMMAND_PHRASE = 'Условия указанной командировки изменены. Ознакомьтесь, пожалуйста, с новыми условиями.'
    
    @pytest.fixture
    def sample_body_new(self):
        return f"""
Вы направлены в командировку с {self.TEST_START_DATE} по {self.TEST_END_DATE}, приказ от {self.TEST_ORDER_DATE} № {self.TEST_ORDER_NUMBER}.
В: {self.TEST_LOCATION}. 
С целью - {self.TEST_PURPOSE}
В случае отмены или изменения командирования необходимо заполнить соответствующую заявку и передать ее в Службу управления
персоналом.

С уважением,
Служба управления персоналом.
"""

    @pytest.fixture
    def sample_body_change(self):
        return f"""
{self.CHANGED_COMMAND_PHRASE}
Вы направлены в командировку с {self.TEST_START_DATE} по {self.TEST_END_DATE}, приказ от {self.TEST_ORDER_DATE} № {self.TEST_ORDER_NUMBER}.
В: {self.TEST_LOCATION}. 
С целью - {self.TEST_PURPOSE}
В случае отмены или изменения командирования необходимо заполнить соответствующую заявку и передать ее в Службу управления
персоналом.

С уважением,
Служба управления персоналом.
"""
    
    @pytest.fixture(autouse=True)
    def setup_parser(self):
        self.parser = EmailParser()
    
    def test_parse_dates(self, sample_body_new, sample_body_change):
        for body, letter in zip((sample_body_new, sample_body_change), (LetterType.NEW, LetterType.UPDATE)):
        
            source_line, start, end, order, letter_type = self.parser._parse_dates(body)
            
            expected_start = datetime.strptime(self.TEST_START_DATE, self.parser.DATES_PATTERN)
            expected_end = datetime.strptime(self.TEST_END_DATE, self.parser.DATES_PATTERN)
            expected_order = datetime.strptime(self.TEST_ORDER_DATE, self.parser.DATES_PATTERN)
            
            assert start == expected_start
            assert end == expected_end  
            assert order == expected_order
            assert letter_type == letter
            assert source_line == sample_body_new.splitlines()[1]
    
    def test_parse_location(self, sample_body_new):
        location = self.parser._parse_location(sample_body_new)
        assert location == self.TEST_LOCATION
    
    def test_parse_order_number(self):
        assert(self.parser._parse_order_number('приказ № 3.') == '3')
        assert(self.parser._parse_order_number('приказ') is None)
        
    def test_parse_purpose(self, sample_body_new):
        purpose = self.parser._parse_purpose(sample_body_new)
        assert purpose == self.TEST_PURPOSE
        
    def test_valid_parse_and_check_for_errors(self):
        source_line_dates = ('1', '2', '3', '4', '5')
        order_num = '6'
        location = '7'
        purpose = '8'
        self.parser._parse_dates = Mock(return_value=source_line_dates)
        self.parser._parse_order_number = Mock(return_value=order_num)
        self.parser._parse_location = Mock(return_value=location)
        self.parser._parse_purpose = Mock(return_value=purpose)
        
        assert self.parser._parse_and_check_for_errors(Mock()) == (*source_line_dates[1:], order_num, location, purpose)
    
    @pytest.mark.parametrize('dates,order_num,location,purpose,expected_error_field', [
        (('line', None, "02.01.2024", "03.01.2024", 'new'), "123", "Москва", "Цель", "дата начала"),        # нет дат
        (('line', "02.01.2024", None, "02.01.2024", 'new'), "123", "Москва", "Цель", "дата окончания"),        # нет дат
        (('line', "02.01.2024", "02.01.2024", None, 'new'), "123", "Москва", "Цель", "дата приказа"),        # нет дат
        (("line", "01.01.2024", "02.01.2024", "03.01.2024", 'new'), None, "Москва", "Цель", "номер приказа"),
        (("line", "01.01.2024", "02.01.2024", "03.01.2024", 'new'), '123', None, "Цель", "место командирования"),
        (("line", "01.01.2024", "02.01.2024", "03.01.2024", 'new'), '123', 'Москва', None, "цель командирования"),
    ])
    def test_failure_parse_and_check_for_errors(self, dates, order_num, location, purpose, expected_error_field):
        self.parser._parse_dates = Mock(return_value=dates)
        self.parser._parse_order_number = Mock(return_value=order_num)
        self.parser._parse_location = Mock(return_value=location)
        self.parser._parse_purpose = Mock(return_value=purpose)
        
        with pytest.raises(ValueError) as exc_info:
            self.parser._parse_and_check_for_errors(Mock())
            
        assert expected_error_field in str(exc_info.value)
        
    def test_parse_success(self):
        parse_result = (
            '01.01.2025',
            '02.01.2025',
            '03.01.2025',
            'new',
            'order',
            'Moscow',
            'target'
        )
        self.parser._parse_and_check_for_errors = Mock(return_value=parse_result)
        mock_email = Mock(spec=EmailData)
        result = self.parser.parse(mock_email)
        
        assert isinstance(result, CommandTrip)
        assert result.email_data == mock_email 
        assert result.start_date == parse_result[0]
        assert result.end_date == parse_result[1]
        assert result.order_date == parse_result[2]
        assert result.letter_type == parse_result[3]
        assert result.order_number == parse_result[4]
        assert result.location == parse_result[5]
        assert result.purpose == parse_result[6]
        
    def test_parse_exception(self):
        self.parser._parse_and_check_for_errors = Mock(side_effect=ValueError('Ошибка'))
        
        with pytest.raises(ValueError) as exc_info:
            self.parser.parse(Mock(spec=EmailData))
            
        assert "Ошибка" in str(exc_info.value)