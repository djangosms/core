from djangosms.core.transports import Message

class Dummy(Message):
    name = None

    def __init__(self, name="dummy", **kwargs):
        type(self).name = name
        Message.__init__(self, name, **kwargs)
