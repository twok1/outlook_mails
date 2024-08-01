import win32com.client
import datetime, os, json
from dateutil.parser import *
import schedule, time

# messages = [
#         {
#             'dates': {'start': None, 'end': None},
#             'order': {'date': None, 'code': None},
#             'destination': None,
#             'target': None,
#             'notifications': {'start': [], 'end': []}
#         },
#     ]

FUCKING_OUT =  range(5, 25)
START_NOTIFICATION = [-1]
END_NOTIFICATION = [-3]


class FakeOutlook:
    def __init__(self, text: str) -> None:
        if len(text.splitlines()) > 0:
            self.SenderName = text.splitlines()[0]
            self.Body = text.splitlines()[1:]
        else:
            self.SenderName = None
            self.Body = None

    def __str__(self) -> str:
        return f'{self.SenderName}\n{self.Body}'
    
    def __repr__(self) -> str:
        return f'{self.SenderName}\n{self.Body}'


class Order:
    def __init__(self, date: datetime.datetime, code: str) -> None:
        self.date = date
        self.code = code

    def __str__(self) -> str:
        return f'{self.code} от {datetime_to_date(self.date)}'
    
    def __repr__(self) -> str:
        return self.__str__


class TaskDates:
    def __init__(self, start: datetime.datetime, end: datetime.datetime) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f'{datetime_to_date(self.start)} - {datetime_to_date(self.end)}'
    
    def __repr__(self) -> str:
        return self.__str__


class Notifications:
    def __init__(self) -> None:
        self.start = START_NOTIFICATION
        self.end = END_NOTIFICATION


class Tasking:
    def __init__(self, msg: FakeOutlook) -> None:
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

    def __str__(self) -> str:
        return f'{self.order}\n{self.dates}\n{self.target}'

    def __repr__(self) -> str:
        return self.__str__
    
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
    

def date_to_datetime(d: str) -> datetime.datetime:
    return datetime.datetime.strptime(d, '%d.%m.%Y')

def datetime_to_date(d: datetime.datetime) -> str:
    return datetime.datetime.strftime(d, '%d.%m.%Y')

def fake_read_mails() -> list:
    mails: list[FakeOutlook] = []

    for file in os.listdir('./mails/'):
        with open(f'./mails/{file}', 'r', encoding='utf-8') as f:
             mails.append(FakeOutlook(f.read()))
    i = 0
    while i < len(mails):
        msg = mails[i]
        if msg.SenderName != 'Уведомления о кадровых мероприятиях':
            mails.pop(i)
        else:
            i += 1
    return mails

def norm_read_mails() -> list:
    '''читаем почту'''
    messages = []
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6).Items  # 6- папка Входящие Outlook
    msg = inbox.GetLast() # последнее письмо в ящике
    while msg :
        subject = str(msg.Subject) # тема письма
        msg_date = datetime.datetime.strptime(str(msg.SentOn)[0:19], '%Y-%m-%d %H:%M:%S')
        # to_list = str(msg.To).split(';') # список получателей
        sender = msg.SenderName # отправитель
        text = str(msg.Body.splitlines()) # текст письма
        # html_text = str(msg.HTMLBody) # html код письма
        if sender == 'Уведомления о кадровых мероприятиях' and subject == 'Информирование о направлении в командировку':
            messages.append(msg)
        msg = inbox.GetPrevious() # переход к следующему письму
    return messages

def form_tasks(mails) -> list[Tasking]:
    tasks: list[Tasking] = []
    for msg in mails:
        tasks.append(Tasking(msg))
    tasks = sorted(tasks, key= lambda x: x.order.date)
    i, k = 0, 0
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
        #grab the date from the meeting time
        if a.Subject.startswith('[командировка напоминание]'):
            com_tasks.append(a)
            # print(dir(a))
            # print(a.AllDayEvent)
            # print(a.Start)
            # print(a.Subject)
            # print(a.ReminderMinutesBeforeStart)
    return com_tasks


def analize_tasks(mail_tasks: list[Tasking], now_tasks):
    need_tasks: list[Tasking] = []
    for mt in mail_tasks:
        nots = [m for m in mt.ret_notifications()]
        for nt in now_tasks:
            if nt.Subject.startswith('[командировка напоминание]'):
                k = datetime.datetime.strptime(str(parse(str(nt.Start)).date()), '%Y-%m-%d')
                if k in nots:
                    nots.remove(k)
                    # nt.Delete
                    # break
            if not nots:
                break
        if nots:
            need_tasks.append(mt)
    return need_tasks


def make_tasks(need_tasks: list[Tasking]):
    Outlook = win32com.client.Dispatch("Outlook.Application")
    for task in need_tasks:
        for m in task.ret_notifications():
            mess = Outlook.CreateItem(1)
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
    # mails = fake_read_mails()
    if not mails:
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
    for i in range(1, 60):
    # for ttt in (':00', ':15', ':30', ':45'):
        # t = f':{i:02}'
        schedule.every().hour.at(f':{i:02}').do(main)
    
    while True:
        schedule.run_pending()
        # print('обновление')
        time.sleep(10)
