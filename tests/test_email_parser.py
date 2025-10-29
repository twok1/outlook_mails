from datetime import datetime
import pytest
from unittest.mock import Mock, patch

from src.email_parser import EmailParser, LetterType

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