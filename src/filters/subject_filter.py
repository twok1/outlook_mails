from .outlook_filter import OutlookFilter

class SubjectFilter(OutlookFilter):
    def __init__(self, *subject) -> None:
        self.subject = subject
        super().__init__()
        
    def apply(self, msg):
        return msg.Subject in self.subject