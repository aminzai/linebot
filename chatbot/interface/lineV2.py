from line.client import Client
from line.message import TextMessage as LineTextMessage
from line.message import StickerMessage as LineStickerMessage
from line.message import ImageMessage as LineImageMessage

from chatbot.interface import BaseInterface
from chatbot.interface import Message
from chatbot.interface import User
from chatbot.interface import UserNotFound


class LineV2Interface(BaseInterface):

    MSG_TYPE_TB = {
        'text': Message.Type.TEXT,
        'image': Message.Type.IMAGE,
        'video': Message.Type.VIDEO,
        'audio': Message.Type.AUDIO,
        'location': Message.Type.LOCATION,
        'sticker': Message.Type.STICKER,
        'join': Message.Type.CONTACT,
    }

    def __init__(self, config):
        super(LineV2Interface, self).__init__()
        self.api = Client(**config)

    def _convert_msg_type(self, key):
        return self.MSG_TYPE_TB[key]

    def get_msg_data(self, msg, store_path):
        resp = self.api.get_content(msg.id)
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
        for raw_msg in raw['events']:
            if raw_msg['type'] == 'message':
                mid = raw_msg['message']['id']
                data = raw_msg['message'].get('text')
                mtype = self._convert_msg_type(raw_msg['message']['type'])
                user = User.get_by_id(raw_msg['source']['userId'], self)
                ext = {}
                ext['reply_token'] = raw_msg['replyToken']
                m = Message(
                        mid,
                        data,
                        mtype,
                        user,
                        self,
                        ext=ext,
                )

                ret.append(m)
        return ret

    def send_msg(self, user, rm):
        # XXX need check msg type
        # assert msg.type == Message.Type.TEXT
        reply_token = rm.ext.get('reply_token')
        msg_list = []
        for m in rm.data:
            # self.log.debug(m)
            t = m['type']
            if t == Message.Type.TEXT:
                mm = LineTextMessage(m['text'])
                msg_list.append(mm)
            elif t == Message.Type.IMAGE:
                mm = LineImageMessage(m['path'], m['preview'])
                msg_list.append(mm)
            elif t == Message.Type.STICKER:
                mm = LineStickerMessage(m['package_id'], m['sticker_id'])
                msg_list.append(mm)
            else:
                self.log.debug("NOT SUPPORT TYPE:%s", m['type'])

        if reply_token:
            self.api.reply_msg(reply_token, msg_list)
        else:
            self.api.send_msg(user.id, msg_list)
        # m = LineTextMessage(msg.text)
        # reply_token = msg.ext.get('reply_token')
        # if reply_token:
        #     self.api.reply_msg(reply_token, m)
        # else:
        #     self.api.send_msg(user.id, m)

    def get_user_profile(self, uid):
        resp = self.api.get_profile(uid)

        if resp.status_code == 200:
            d = resp.json()
            return User(uid, d['displayName'], self)
        else:
            raise UserNotFound(uid)
