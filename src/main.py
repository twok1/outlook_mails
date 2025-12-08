import time
import schedule

from .application import Application

def create():
    app = Application()
    app.run()
    del(app)

def main():
    create()
    schedule.every().hour.at('00').do(create)
    while True:
        schedule.run_pending()
        time.sleep(1)