# src/parsers/absence_mail_parser.py
import re
import logging
from datetime import datetime
from typing import List, Optional

from natasha import Segmenter, MorphVocab, NamesExtractor, Doc

from src.models import EmailData, AbsenceData, AbsenceSubstitute, AbsencePeriod
from src.core.interfaces import BaseMailParser

logger = logging.getLogger(__name__)

class AbsenceMailParser(BaseMailParser):
    def __init__(self):
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        # Специализированный парсер русских ФИО
        self.names_extractor = NamesExtractor(self.morph_vocab)
        
        self.date_pattern = re.compile(
            r'с\s+(\d{2})\.(\d{2})(?:\.?(\d{4}))?\.?\s*(?:по|-)\s*(\d{2})\.(\d{2})\.(\d{4})', 
            re.IGNORECASE
        )

    def run(self, messages: List[EmailData]) -> List[AbsenceData]:
        parsed_data = []
        for msg in messages:
            try:
                result = self._parse_single(msg)
                if result:
                    parsed_data.append(result)
            except Exception as e:
                logger.error(f'Ошибка при парсинге отсутствия {msg.message_id}', exc_info=True)
                continue
        return parsed_data

    def _extract_persons(self, text: str) -> List[str]:
        persons = []
        for match in self.names_extractor(text):
            # Жесткое правило: ФИО в официальном документе всегда содержит 
            # минимум фамилию и имя (или инициал). Пропускаем неполные совпадения.
            if not match.fact.last or not match.fact.first:
                continue
                
            name_parts = [match.fact.last.title(), match.fact.first.title()]
            if match.fact.middle:
                name_parts.append(match.fact.middle.title())
                
            persons.append(" ".join(name_parts))
            
        return persons

    def _extract_dates(self, text: str) -> List[AbsencePeriod]:
        periods = []
        for match in self.date_pattern.finditer(text):
            d1, m1, y1, d2, m2, y2 = match.groups()
            start_year = int(y1) if y1 else int(y2)
            try:
                periods.append(AbsencePeriod(
                    start_date=datetime(start_year, int(m1), int(d1)),
                    end_date=datetime(int(y2), int(m2), int(d2))
                ))
            except ValueError:
                continue
        return periods

    def _parse_single(self, msg: EmailData) -> Optional[AbsenceData]:
        # Удаляем приветствие с помощью регулярного выражения до начала любой обработки
        clean_body = re.sub(r'Уважаемые коллеги[!\.,\s]*', '', msg.body, flags=re.IGNORECASE)
        
        # Дробим очищенный текст по абзацам
        raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean_body) if p.strip()]
        
        chunks = []
        for p in raw_paragraphs:
            if ';' in p:
                chunks.extend([c.strip() for c in p.split(';') if c.strip()])
            else:
                chunks.append(p)
                
        if not chunks:
            return None

        main_person = None
        main_person_last_name = None
        main_dates = []
        main_position = "Не определена"
        substitutes = []
        
        # Глобальный поиск базовых дат (на случай, если они оторваны от ФИО)
        all_dates = self._extract_dates(msg.body)
        if all_dates:
            main_dates = [all_dates[0]]

        # Шаг 1: Ищем главного отпускника (первое встреченное ФИО)
        for chunk in chunks:
            persons = self._extract_persons(chunk)
            if persons and not main_person:
                main_person = persons[0]
                main_person_last_name = main_person.split()[0].lower()
                
                # Эвристика для должности (строка без цифр и ФИО)
                cleaned = chunk.replace('Уважаемые коллеги!', '')
                for line in [l.strip(' ,.') for l in cleaned.splitlines() if l.strip()]:
                    line_lower = line.lower()
                    if (not re.search(r'\d', line) and 
                        'отпуск' not in line_lower and 
                        'командировк' not in line_lower and 
                        len(line) > 5 and
                        main_person_last_name not in line_lower):
                        main_position = line
                        break
                break

        if not main_person:
            return None

        # Шаг 2: Ищем заместителей и их даты
        for chunk in chunks:
            chunk_lower = chunk.lower()
            
            # Жестко отсекаем блок с контактами отпускника и подписи отправителей
            if 'доступен' in chunk_lower or 'доступна' in chunk_lower or 'с уважением' in chunk_lower:
                continue
                
            chunk_dates = self._extract_dates(chunk)
            persons = self._extract_persons(chunk)
            
            # Если это блок отпускника и там есть даты - жестко закрепляем их как основные
            if main_person_last_name in chunk_lower and chunk_dates and not any(p.split()[0].lower() != main_person_last_name for p in persons):
                main_dates = chunk_dates

            for person in persons:
                last_name = person.split()[0].lower()
                # Если фамилия не совпадает с фамилией отпускника — это заместитель
                if last_name != main_person_last_name:
                    # Назначаем даты: если в его строке указаны свои даты, берем их. Иначе — основные.
                    sub_dates = chunk_dates if chunk_dates else main_dates
                    
                    # Проверяем на дубликаты
                    exists = False
                    for sub in substitutes:
                        if sub.person == person and sub.dates == sub_dates:
                            exists = True
                            break
                    if not exists:
                        substitutes.append(AbsenceSubstitute(person=person, dates=sub_dates))

        return AbsenceData(
            email_id=msg.message_id,
            main_person=main_person,
            main_position=main_position,
            main_dates=main_dates,
            substitutes=substitutes
        )