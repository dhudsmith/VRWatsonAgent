import json


class SocketMessage:
    """
    Encapsulates all the data to send over websocket to clients
    """
    # members
    def __init__(self, message_type: str = None, note: str = None, meta: dict = None):
        self.type = message_type
        self.note = note
        self.meta = meta

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_string: str):

        class_dict = json.loads(json_string)

        msg = cls(class_dict['type'], class_dict['note'], class_dict['meta'])

        return msg


