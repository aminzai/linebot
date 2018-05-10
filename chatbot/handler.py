import os
import six
import abc
import logging
import yaml
import re
import random
from chatbot.interface import Message
# from chatbot.interface import User
from chatbot.util.singleton import Singleton


class Handler(six.with_metaclass(Singleton, object)):

    class Mode(object):
        NONE = 'none'
        PARTY = 'party'
        BCAST = 'bcast'
        LISTEN = 'listen'

    in_q = []
    out_q = []
    mode = Mode.NONE
    donwload_path = './download/'

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def add(self, msg):
        assert isinstance(msg, Message)
        self.in_q.append(msg)

        # XXX Sync handle
        self.do_parse()

    def do_parse(self):
        while bool(self.in_q):
            in_msg = self.in_q.pop(0)
            self.log.debug(
                "proc str: (%s) %s",
                in_msg.from_user.display_name,
                in_msg.text)
            if in_msg.type == Message.Type.STICKER:
                continue

            mph = MessageParse(in_msg)
            mph.add(MphMsgData)
            mph.add(MphCmd)
            mph.add(MphHelp)
            mph.add(MphModeProc)
            mph.add(MphReply)
            mph.add(MphMsgLog)
            self.out_q.extend(mph.parse())

        # XXX Sync MODE
        self.do_send()

    def do_send(self):
        while bool(self.out_q):
            rm = self.out_q.pop(0)
            if rm is None:
                break
            self.log.debug("out:%s", rm)
            # for u in msg.to_user:
            #     msg.interface.send_msg(u, msg)
            rm.interface.send_msg(rm.user, rm)


class ReplyMessage(object):

    def __init__(self, user, interface, ext=None):
        self.user = user
        self.interface = interface
        self.ext = ext if ext else {}
        self.data = []

    def add_text(self, text):
        d = {
            'type': Message.Type.TEXT,
            'text': text
        }
        self.data.append(d)

    def add_sticker(self, package_id, sticker_id):
        d = {
            'type': Message.Type.STICKER,
            'package_id': package_id,
            'sticker_id': sticker_id,
            }
        self.data.append(d)

    def add_image(self, path, preview):
        d = {
            'type': Message.Type.IMAGE,
            'path': path,
            'preview': preview,
            }
        self.data.append(d)


class ReplyInfo(six.with_metaclass(Singleton, object)):

    def __init__(self):
        self.match_reply_tab = {}
        self.match_help_list = []
        self.ldx_list = []
        with open('reply.yml', 'r') as fd:
            self.info = yaml.load(fd)

        for info in self.info.get('pattern', []):
            for k in info['key']:
                prog = re.compile(k)
                self.match_reply_tab[prog] = info['msg']

        self.ldx_list = self.info['ldx']

        help_text_list = []
        for info in self.info.get('pattern', []):
            cmd = info['key'][0]
            try:
                text = info['help']
            except KeyError:
                continue
            else:
                t = '({cmd}) {text}'.format(cmd=cmd, text=text)
                help_text_list.append(t)
        self.help_text = '\n'.join(help_text_list)

        for help_pattern in self.info['help']['key']:
            prog = re.compile(help_pattern)
            self.match_help_list.append(prog)

    def match_reply(self, text):
        for key, value in six.iteritems(self.match_reply_tab):
            if key.search(text):
                return value

        # ldx mode
        info = random.choice(self.ldx_list)
        return info['msg']

    def match_help(self, text):
        for p in self.match_help_list:
            if p.match(text):
                return self.help_text
        return None


class MessageParseHandler(six.with_metaclass(abc.ABCMeta, object)):

    def __init__(self, msg):
        self.log = logging.getLogger(__name__)
        self.msg = msg

    @abc.abstractmethod
    def execute(self):
        pass


class MphMsgData(MessageParseHandler):

    def _gen_path(self):
        hdr = Handler()
        ext = ''
        if self.msg.type == Message.Type.IMAGE:
            ext = '.jpg'
        name = '{interface}-{id}{ext}'.format(
            interface=self.msg.interface.__class__.__name__,
            id=self.msg.id,
            ext=ext)
        try:
            os.makedirs(hdr.donwload_path)
        except FileExistsError:
            pass
        return os.path.join(hdr.donwload_path, name)

    def execute(self):
        if self.msg.type == Message.Type.IMAGE:
            path = self._gen_path()
            self.msg.interface.get_msg_data(self.msg, path)
            self.msg.text = path
        return [], True


class MphModeProc(MessageParseHandler):

    def execute(self):
        hdr = Handler()
        ret = []
        """
        if hdr.mode == Handler.Mode.LISTEN:
            m = self.msg.copy()
            user_list = User.get_all_admin(m.interface)
            m.to_user = user_list
            return [m], True
        """
        if hdr.mode == Handler.Mode.PARTY:
            rm = ReplyMessage(
                self.msg.from_user, self.msg.interface, self.msg.ext)
            rm.add_text('將您資料上傳摟！晚點就可以在投影機上看到！')
            return [rm], True
            # m = self.msg.copy()
            # m.text = '將您資料上傳摟！晚點就可以在投影機上看到！'
            # m.to_user = [m.from_user]
            # return [m], Flase
        return ret, True


class MphMsgLog(MessageParseHandler):

    def execute(self):
        hdr = Handler()
        Message.save(self.msg, hdr.mode)
        return [], True


class MphHelp(MessageParseHandler):

    def execute(self):
        ret = []
        ri = ReplyInfo()
        hi = ri.match_help(self.msg.text)
        if hi:
            rm = ReplyMessage(
                self.msg.from_user, self.msg.interface, self.msg.ext)
            rm.add_text(hi)
            return [rm], False
        return ret, True


class MphReply(MessageParseHandler):

    def execute(self):
        ret = []
        hdr = Handler()
        if hdr.mode == Handler.Mode.NONE:
            ri = ReplyInfo()
            mt = ri.match_reply(self.msg.text)
            if mt:
                rm = ReplyMessage(
                    self.msg.from_user, self.msg.interface, self.msg.ext)
                for mi in mt:
                    t = mi['type']
                    if t == Message.Type.TEXT:
                        rm.add_text(mi['data'])
                    elif t == Message.Type.IMAGE:
                        rm.add_image(**mi['data'])
                    elif t == Message.Type.STICKER:
                        rm.add_sticker(**mi['data'])
                ret.append(rm)
        return ret, True


class MphCmd(MessageParseHandler):

    prog_cmd_set_mode_none = re.compile('\/set\smode\snone')
    prog_cmd_set_mode_party = re.compile('\/set\smode\sparty')
    prog_cmd_set_mode_bcast = re.compile('\/set\smode\sbcast')
    prog_cmd_set_mode_listen = re.compile('\/set\smode\slisten')
    prog_cmd_get_mode = re.compile('\/get\smode')

    def _gen_mode_info(self, msg):
        hdr = Handler()
        text = 'Mode={}'.format(hdr.mode)
        rm = ReplyMessage(
            msg.from_user, msg.interface, msg.ext)
        rm.add_text(text)
        return rm
        # m = Message(
        #     msg.id,
        #     text,
        #     Message.Type.TEXT,
        #     msg.from_user,
        #     msg.interface,
        #     [msg.from_user],
        #     ext=self.msg.ext,
        # )
        # return m

    def _cmd_get_mode(self, msg):
        return self._gen_mode_info(msg)

    def _cmd_set_mode_none(self, msg):
        hdr = Handler()
        hdr.mode = Handler.Mode.NONE
        return self._gen_mode_info(msg)

    def _cmd_set_mode_party(self, msg):
        hdr = Handler()
        hdr.mode = Handler.Mode.PARTY
        return self._gen_mode_info(msg)

    def _cmd_set_mode_bcast(self, msg):
        hdr = Handler()
        hdr.mode = Handler.Mode.BCAST
        return self._gen_mode_info(msg)

    def _cmd_set_mode_listen(self, msg):
        hdr = Handler()
        hdr.mode = Handler.Mode.LISTEN
        return self._gen_mode_info(msg)

    CMD_TAB = {
        prog_cmd_get_mode: _cmd_get_mode,
        prog_cmd_set_mode_none: _cmd_set_mode_none,
        prog_cmd_set_mode_party: _cmd_set_mode_party,
        prog_cmd_set_mode_bcast: _cmd_set_mode_bcast,
        prog_cmd_set_mode_listen: _cmd_set_mode_listen,
    }

    def execute(self):
        for prog, func in six.iteritems(self.CMD_TAB):
            if prog.match(self.msg.text):
                # self.log.debug('hit')
                return ([func(self, self.msg)], False)
        return [], True


class MessageParse(object):

    def __init__(self, msg):
        self.msg = msg
        self.mph_q = []

    def add(self, mph):
        self.mph_q.append(mph)

    def parse(self):
        replay_q = []

        for mph in self.mph_q:
            reply_list, do_next = mph(self.msg).execute()
            replay_q.extend(reply_list)
            if not do_next:
                break
        return replay_q
