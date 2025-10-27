from src.email_reader import EmailReader


class Application:
    def __init__(self) -> None:
        self.mail_reader = EmailReader()
    
    def run(self):
        pass