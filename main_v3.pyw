import win32com.client
import datetime, os, json
from dateutil.parser import *
import schedule, time
import configparser
from pathlib import Path


SCRIPT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_mails.ini'))

config = configparser.ConfigParser()
config.read(SCRIPT_PATH, encoding='utf-8')
FUCKING_OUT =  (int(config.get('mails', 'END_LOCK')), int(config.get('mails', 'START_LOCK')))
START_NOTIFICATION = list([i for i in map(int, config.get('mails', 'START_NOTIFICATION').split(', '))])
END_NOTIFICATION = list([i for i in map(int, config.get('mails', 'END_NOTIFICATION').split(', '))])
WORKING_RANGE = tuple([i for i in map(int, config.get('mails', 'WORKING_RANGE').split(', '))])
# FUCKING_OUT = (5, 25)
# START_NOTIFICATION = [-7, -3, -1]
# END_NOTIFICATION = [-7, -3, -1]
# WORKING_RANGE = (0, 15, 30, 45)

# WORKING_RANGE = range(60)


class FakeOutlook:
    # фэйковый аутлук. использовал для отладки
    def __init__(self, text: str) -> None:
        if len(text.splitlines()) > 0:
            self.SenderName = text.splitlines()[0]
            self.Body = text.splitlines()[1:]
        else:
            self.SenderName = None
            self.Body = None
    
    def __repr__(self) -> str:
        return f'{self.SenderName}\n{self.Body}'


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
        self.start = START_NOTIFICATION.copy()
        self.end = END_NOTIFICATION.copy()


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
            while (self.dates.end + datetime.timedelta(d)).day <= FUCKING_OUT[0] \
                    or (self.dates.end + datetime.timedelta(d)).day >= FUCKING_OUT[1]:
                self.notifications.end[k] -= 1
                d = self.notifications.end[k]
            k += 1

        s = [self.dates.start + datetime.timedelta(i) for i in self.notifications.start]
        e = [self.dates.end + datetime.timedelta(i) for i in self.notifications.end]
        return list(set(s + e))
    
def date_to_datetime(d: str) -> datetime.datetime:
    return datetime.datetime.strptime(d, '%d.%m.%Y')

def datetime_to_date(d: datetime.datetime) -> str:
    return datetime.datetime.strftime(d, '%d.%m.%Y')

def norm_read_mails() -> list:
    '''читаем почту'''
    messages = []
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6).Items  # 6- папка Входящие Outlook
    for msg in inbox:
        if msg.Class != 52:
            subject = str(msg.Subject) # тема письма
            sender = msg.SenderName # отправитель
            if sender == 'Уведомления о кадровых мероприятиях' and subject == 'Информирование о направлении в командировку':
                messages.append(msg)
    return messages

def form_tasks(mails) -> list[Tasking]:
    tasks: list[Tasking] = []
    for msg in mails:
        tasks.append(Tasking(msg))
    tasks = sorted(tasks, key= lambda x: x.order.date)
    i, k = 0, 0
    # анализ командировок на перекрытие (изменения) и удаление лишних
    while i < len(tasks):
        while k < len(tasks):
            if i != k:
                if tasks[i].dates.start <= tasks[k].dates.end or tasks[i].dates.end >= tasks[k].dates.start:
                    if tasks[i].order.date < tasks[k].order.date and \
                            (tasks[i].destination == tasks[k].destination and tasks[i].target == tasks[k].target):
                        tasks[i] = tasks[k]
                        tasks.pop(k)
                        k -= 1
            k += 1
        i += 1
        k = i + 1

    return tasks


def read_tasks():
    Outlook = win32com.client.Dispatch("Outlook.Application")
    
    ns = Outlook.GetNamespace("MAPI")
    appointments = ns.GetDefaultFolder(9).Items
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = "True"
    com_tasks = []
    for a in appointments:
        if a.Subject.startswith('[командировка напоминание]'):
            com_tasks.append(a)
    return com_tasks


def analize_tasks(mail_tasks: list[Tasking], now_tasks):
    need_tasks: list[Tasking] = []
    for mt in mail_tasks:
        nots = [m for m in mt.ret_notifications()]
        for nt in now_tasks:
            if nt.Subject.startswith(f'[командировка напоминание]'):
                k = datetime.datetime.strptime(str(parse(str(nt.Start)).date()), '%Y-%m-%d')
                if k in nots:
                    nots.remove(k)
            if not nots:
                break
        if nots:
            need_tasks.append(mt)
    return need_tasks


def make_tasks(need_tasks: list[Tasking]):
    outlook = win32com.client.Dispatch("Outlook.Application")
    for task in need_tasks:
        for m in task.ret_notifications():
            # if datetime.timedelta(hours=3) + m >= datetime.datetime.now() - datetime.timedelta(days=1):
            mess = outlook.CreateItem(1)
            mess.Start = datetime.timedelta(hours=3) + m
            mess.ReminderMinutesBeforeStart = 15
            mess.Duration = 90
            mess.AllDayEvent = True
            mess.Subject = f'[командировка напоминание] {task.order}'
            mess.Body = f"{task.dates}\n{task.target}\n{task.destination}"
            mess.Save()


def main():
    # считываем письма с аутлука
    print('Обновление Outlook')
    mails = norm_read_mails()
    # преобразовываем их в элементы заданий и обрабатываем 
    mail_tasks = form_tasks(mails)
    # считываем текущие задачи из аутлука
    now_tasks = read_tasks()
    # сравниваем имеющиеся и необходимые задачи
    need_tasks = analize_tasks(mail_tasks, now_tasks)
    # make tasks
    make_tasks(need_tasks)



def jobs():
    print('working')

    

if __name__ == '__main__':
    # main()
    print('Работаем')
    for i in range(1, 60):
    # for i in WORKING_RANGE:
        # t = f':{i:02}'
        schedule.every().hour.at(f':{i:02}').do(main)
    
    while True:
        schedule.run_pending()
        # print('обновление')
        time.sleep(3)
