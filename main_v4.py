import win32com.client
import datetime, os, json
from dateutil.parser import *
import schedule, time



FUCKING_OUT =  range(5, 25)
START_NOTIFICATION = [-1]
END_NOTIFICATION = [-3]


class Order:
    # класс приказа на командировку
    def __init__(self, date: datetime.datetime, code: str) -> None:
        self.date = date
        self.code = code

    def __repr__(self) -> str:
        return f'{self.code} от {datetime_to_date(self.date)}'


class TaskDates:
    # класс дат командирования
    def __init__(self, start: datetime.datetime, end: datetime.datetime) -> None:
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f'{datetime_to_date(self.start)} - {datetime_to_date(self.end)}'


class Notifications:
    # класс с временами напоминаний
    def __init__(self) -> None:
        self.start = START_NOTIFICATION
        self.end = END_NOTIFICATION


class Tasking:
    def __init__(self, msg) -> None:
        self.sender = msg.SenderName
        for line in msg.Body.splitlines():
            if 'Вы направлены в командировку' in line:
                self.order = Order(date_to_datetime(line[67:77]), line[78:-1])
                self.dates = TaskDates(date_to_datetime(line[31:41]), date_to_datetime(line[45:55]))
            elif line.startswith('В: '):
                self.destination = line[3:] 
            elif line.startswith('С целью - '):
                self.target = line[10:]
                self.notifications = Notifications()

    def __repr__(self) -> str:
        return f'{self.order}\n{self.dates}\n{self.target}'
    
    def ret_notifications(self):
        k = 0
        while k < len(self.notifications.end):
            d = self.notifications.end[k]
            while (self.dates.end + datetime.timedelta(d)).day not in FUCKING_OUT:
                self.notifications.end[k] -= 1
                d = self.notifications.end[k]
            k += 1

        s = [self.dates.start + datetime.timedelta(i) for i in self.notifications.start]
        e = [self.dates.end + datetime.timedelta(i) for i in self.notifications.end]
        return s + e
    
    @classmethod
    def date_to_datetime(d: str) -> datetime.datetime:
        return datetime.datetime.strptime(d, '%d.%m.%Y')

    @classmethod
    def datetime_to_date(d: datetime.datetime) -> str:
        return datetime.datetime.strftime(d, '%d.%m.%Y')


def main():
    


if __name__ == '__main__':
    main()