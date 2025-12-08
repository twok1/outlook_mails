from .outlook_filter import OutlookFilter

class SenderEmailFilter(OutlookFilter):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__()
        
    def apply(self, msg):
        return msg.SenderEmailAddress == self.email