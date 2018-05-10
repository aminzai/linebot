from linebot.client import LineBotClient

from chatbot.interface import BaseInterface
from chatbot.interface import Message
from chatbot.interface import User
from chatbot.interface import UserNotFound


class LineInterface(BaseInterface):

    MSG_TYPE_TB = {
        1: Message.Type.TEXT,
        2: Message.Type.IMAGE,
        3: Message.Type.VIDEO,
        4: Message.Type.AUDIO,
        7: Message.Type.LOCATION,
        8: Message.Type.STICKER,
        10: Message.Type.CONTACT,
    }

    def __init__(self, config):
        super(LineInterface, self).__init__()
        self.api = LineBotClient(**config)

    def _convert_msg_type(self, key):
        return self.MSG_TYPE_TB[key]

    def get_msg_data(self, msg, store_path):
        resp = self.api.get_message_content(msg.id)
        if resp.status_code == 200:
            with open(store_path, 'wb') as fd:
                for chunk in resp.iter_content(1024):
                    fd.write(chunk)
            return True
        else:
            return False

    def recv_msg(self, raw):
        self.log.debug('RECV: %s', raw)
        ret = []
        for raw_msg in raw['result']:
            m = Message(
                raw_msg['content']['id'],
                raw_msg['content']['text'],
                self._convert_msg_type(raw_msg['content']['contentType']),
                User.get_by_id(raw_msg['content']['from'], self),
                self
            )
            ret.append(m)
        return ret

    def send_msg(self, user, msg):
        # XXX need check msg type
        assert msg.type == Message.Type.TEXT
        self.api.send_text(to_mid=user.id, text=msg.text)

    def get_user_profile(self, uid):
        raw = self.api.get_user_profile(uid)
        if len(raw) == 1:
            d = raw[0]
            return User(uid, d['display_name'], self)
        else:
            raise UserNotFound(uid)
