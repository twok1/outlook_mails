import time
import schedule

from .application import Application

def create():
    app = Application()
    try:
        app.run()
    except:
        time.sleep(60)
    del(app)

def main():
    create()
    schedule.every().hour.at('00:00').do(create)
    while True:
        schedule.run_pending()
        time.sleep(1)