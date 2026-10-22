# src/parsers/vacation_mail_parser.py
import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from src.models import EmailData, VacationData, VacationSubstitute
from src.core.interfaces import BaseMailParser

logger = logging.getLogger(__name__)

class VacationMailParser(BaseMailParser):
    def __init__(self):
        # Добавили \.? перед закрывающей скобкой, чтобы "съедать" случайные точки в конце (например, 22.09.)
        self.date_pattern = re.compile(r'с\s+(\d{2}\.\d{2}(?:\.\d{4})?\.?)\s+по\s+(\d{2}\.\d{2}\.\d{4})', re.IGNORECASE)
        self.fio_pattern = re.compile(r'^[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2}$|^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.$', re.UNICODE)
        
        # Убрали предлог "на", теперь реагирует и на "В период", и на "На период"
        self.substitute_markers = ['и.о.', 'исполнение обязанностей', 'период отсутствия', 'возложено']

    def run(self, messages: List[EmailData]) -> List[VacationData]:
        parsed_data = []
        for msg in messages:
            try:
                result = self._parse_single(msg)
                if result:
                    parsed_data.append(result)
            except Exception as e:
                logger.error(f'Ошибка при парсинге отпуска {msg.message_id}', exc_info=True)
                continue
        return parsed_data

    def _extract_dates(self, text: str) -> List[str]:
        matches = self.date_pattern.findall(text)
        # rstrip('.') аккуратно удалит лишнюю точку, если она прилипла к дате
        return [f"с {m[0].rstrip('.')} по {m[1]}" for m in matches]

    def _extract_person_and_position(self, text: str) -> Tuple[Optional[str], str]:
        """Умный поиск ФИО и должности на основе эвристики."""
        cleaned = text.replace('Уважаемые коллеги!', '')
        lines = [line.strip(' ,.') for line in cleaned.splitlines() if line.strip()]
        
        person = None
        position = "Не определена"
        
        for line in lines:
            if not line:
                continue
                
            # Если похоже на ФИО и мы еще не нашли его
            if not person and self.fio_pattern.match(line.strip()):
                person = line.strip()
            # Если не содержит цифр, не является ключевой фразой, достаточно длинное и это не найденное ФИО - это должность
            elif (not re.search(r'\d', line) and 
                  'отпуск' not in line.lower() and 
                  'командировк' not in line.lower() and 
                  len(line) > 5 and 
                  line != person):
                if position == "Не определена":
                    position = line
                    
        return person, position

    def _parse_single(self, msg: EmailData) -> Optional[VacationData]:
        # Разделяем по двойному переносу строки или по ключевым фразам абзацев
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', msg.body) if p.strip()]
        
        if not paragraphs:
            return None

        # Обрабатываем основную информацию (первые абзацы до заместителей)
        main_text_block = " ".join(paragraphs[:2])
        person, position = self._extract_person_and_position(main_text_block)
        dates = self._extract_dates(main_text_block)
        
        if not person:
             return None # Если не нашли человека, пропускаем

        vacation = VacationData(
            email_id=msg.message_id,
            main_person=person,
            main_position=position,
            main_dates=dates,
            substitutes=[]
        )

        # Анализ заместителей
        for p in paragraphs[2:]:
            p_lower = p.lower()
            if any(marker in p_lower for marker in self.substitute_markers):
                sub_person, _ = self._extract_person_and_position(p)
                if sub_person:
                    sub_dates = self._extract_dates(p)
                    final_dates = sub_dates if sub_dates else dates
                    
                    vacation.substitutes.append(
                        VacationSubstitute(person=sub_person, dates=final_dates)
                    )

        return vacation