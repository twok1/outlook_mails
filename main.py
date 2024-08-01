import win32com.client
import datetime, os, json
from dateutil.parser import *


# def 
DEFAULT_NOTIFICATIONS = {'start': [0], 'end': []}
# messages = [
#         {
#             'dates': {'start': None, 'end': None},
#             'order': {'date': None, 'code': None},
#             'destination': None,
#             'target': None,
#             'notifications': {'start': [], 'end': []}
#         },
#     ]

class OutlookMailTask:
    def __init__(self) -> None:
        pass

def serialize_mess(mess, order_code, start_date, end_date, order_date, target, destination):
    mess['dates']['start'] = start_date
    mess['dates']['end'] = end_date
    mess['order']['date'] = order_date
    mess['order']['code'] = order_code
    mess['destination'] = destination
    mess['target'] = target
    if mess['notifications'] == {'start': [], 'end': []}:
        mess['notifications'] = DEFAULT_NOTIFICATIONS
    return mess

def message_parsing(msg, messages):
    # new = 1, change = 2, abort = 3

    for line in msg.splitlines():
        if 'Вы направлены в командировку' in line:
            start_date = line[31:41]
            end_date = line[45:55]
            order_date = line[67:77]
            order_code = line[78:-1]
        if line.startswith('В: '):
            destination = line[3:] 
        if line.startswith('С целью - '):
            target = line[10:]
    put_in = False
    msg_info = order_code, start_date, end_date, order_date, target, destination
    for mess in messages:
        if mess['order']['code'] == order_code:
            mess = serialize_mess(mess, *msg_info)
            put_in = True
    if not put_in:
        mess = serialize_mess(mess, *msg_info)
    print(messages)


    print(f'с {start_date} до {end_date} по {order_code} от {order_date}\nв {destination}\nцель: {target}')
    return messages


    # com_type = 0
    # if 'Условия указанной командировки изменены' in msg:
    #     com_type = 2
    # for m in messages:
    #     print(m)

def analing_messages(messages):
    '''проверка на перекрытие дат'''
    return messages

def read_mails(messages):
    '''читаем почту'''
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6).Items  # 6- папка Входящие Outlook
    msg = inbox.GetLast() # последнее письмо в ящике
    while msg :
        subject = str(msg.Subject) # тема письма
        msg_date = datetime.datetime.strptime(str(msg.SentOn)[0:19], '%Y-%m-%d %H:%M:%S')
        # to_list = str(msg.To).split(';') # список получателей
        sender = msg.SenderName # отправитель
        text = str(msg.Body) # текст письма
        # html_text = str(msg.HTMLBody) # html код письма
        if sender == 'Уведомления о кадровых мероприятиях':
            messages = message_parsing(text, messages)
        msg = inbox.GetPrevious() # переход к следующему письму
    return messages

def get_file():
    '''считываем данные из файла'''
    messages = [
        {
            'dates': {'start': None, 'end': None},
            'order': {'date': None, 'code': None},
            'destination': None,
            'target': None,
            'notifications': {'start': [], 'end': []}
        },
    ]
    if os.path.exists('./dump.json'):
        with open('./dump.json', 'r', encoding='utf-8') as f: 
            messages = json.load(f)
    return messages

def write_file(messages):
    with open('./dump.json', 'w', encoding='utf-8') as f:
        json.dump(messages, f)

def read_tasks():
    Outlook = win32com.client.Dispatch("Outlook.Application")
    
    ns = Outlook.GetNamespace("MAPI")
    appointments = ns.GetDefaultFolder(9).Items
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = "True"
    com_tasks = []
    for a in appointments:
        #grab the date from the meeting time
        if a.Subject.startswith('[командировка]'):
            com_tasks.append(a)
            # print(dir(a))
            # print(a.AllDayEvent)
            # print(a.Start)
            # print(a.Subject)
            # print(a.ReminderMinutesBeforeStart)
    return com_tasks

def serialize_tasks(com_tasks, messages):
    need_tasks = []
    for mess in messages:
        gw = False
        for task in com_tasks:
            if task.Subject[15:] == mess['order']['code']:
                gw = True
                break
        if not gw:
            need_tasks.append(mess)
    return need_tasks

def make_tasks(need_tasks):
    Outlook = win32com.client.Dispatch("Outlook.Application")
    for task in need_tasks:
        for period in ('start', 'end'):
            for m in task['notifications'][period]:
                mess = Outlook.CreateItem(1)
                mess.Start = datetime.datetime.strptime(task['dates'][period], '%d.%m.%Y') + datetime.timedelta(hours=3) + datetime.timedelta(days=m)
                mess.ReminderMinutesBeforeStart = 15
                mess.Duration = 90
                mess.AllDayEvent = True
                mess.Subject = f'[командировка] {task["order"]["code"]}'
                mess.Body = f"{task['target']}\n {task['destination']}"
                mess.Save()


def main():
    messages = get_file()
    messages = read_mails(messages)
    messages = analing_messages(messages=messages)
    write_file(messages)

    com_tasks = read_tasks()
    need_tasks = serialize_tasks(com_tasks, messages)
    make_tasks(need_tasks)
    print(need_tasks)
    

def test_main():
    Outlook = win32com.client.Dispatch("Outlook.Application")


    ns = Outlook.GetNamespace("MAPI")
    appointments = ns.GetDefaultFolder(9).Items
    appointments.Sort("[Start]")
    appointments.IncludeRecurrences = "True"
    for a in appointments:
        #grab the date from the meeting time
        meetingDate = str(a.Start)
        subject = str(a.Subject)
        body = str(a.Body.encode("utf8"))
        duration = str(a.Duration)
        date = parse(meetingDate).date()
        time = parse(meetingDate).time()
        participants = []
        for r in a.Recipients:
            participants += [str(r)]
        # print(dir(a))
        print(a.AllDayEvent)
        print(a.Start)
        print(a.Subject)
        print(a.ReminderMinutesBeforeStart)
        # print(str(a))


    
    mess = Outlook.CreateItem(1)
    # print(datetime.datetime.now())
    mess.Start = datetime.datetime.now() + datetime.timedelta(hours=3, minutes=17)
    mess.ReminderMinutesBeforeStart = 0
    mess.Duration = 90
    mess.AllDayEvent = True
    mess.Subject = 'FUCK YOU'
    # mess.Display(True)
    mess.Save()
    print(dir(mess))


if __name__ == '__main__':
    main()
    # test_main()