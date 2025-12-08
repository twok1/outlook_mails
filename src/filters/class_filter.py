from .outlook_filter import OutlookFilter

class ClassFilter(OutlookFilter):
    def __init__(self, class_: int) -> None:
        self.class_ = class_
        super().__init__()
        
    def apply(self, msg):
        return msg.Class != self.class_