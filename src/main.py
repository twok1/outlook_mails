import schedule

from .application import Application

def create():
    try:
        app = Application()
        app.run()
    except:
        pass
    del(app)

def main():
    create()
    schedule.every().hour.at('00').do(create)
    while True:
        schedule.run_pending()