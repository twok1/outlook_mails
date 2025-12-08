import time
from .application import Application

def main():
    app = Application()
    app.run()
    time.sleep(900)
    app.run()