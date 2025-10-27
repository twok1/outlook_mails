from src.email_parser import EmailParser
from src.email_reader import EmailReader


class Application:
    def __init__(self) -> None:
        self.mail_reader = EmailReader()
        self.mail_parser = EmailParser()
    
    def run(self):
        messages = self.mail_reader.run()
        parser_messages = self.mail_parser.run(messages)
        pass