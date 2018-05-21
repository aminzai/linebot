import abc
import six
import logging
import sqlalchemy
import datetime
import json
from sqlalchemy.sql.expression import func
from chatbot.model.user import User as UserDb
from chatbot.model.message import Message as MessageDb
from chatbot.model import db_session


class InterfaceNotFound(Exception):
    pass


class UserNotFound(Exception):
    pass


INTERFACE_STORE = {}


class Message(object):

    class Type(object):
        TEXT = 1
        IMAGE = 2
        VIDEO = 3
        AUDIO = 4
        LOCATION = 5
        STICKER = 6
        CONTACT = 7
        HELP = 8
        UNKNOWN = 999

    def __init__(
            self, mid, text, msg_type, from_user, interface,
            to_user=None, ext=None):
        self.id = mid
        self.text = text
        self.type = msg_type
        self.from_user = from_user
        self.to_user = to_user if to_user else []
        self.interface = interface
        self.ext = ext if ext else {}

    def copy(self):
        return Message(
            self.id,
            self.text,
            self.type,
            self.from_user,
            self.interface,
            to_user=self.to_user,
            ext=self.ext,
        )

    @staticmethod
    def save(msg, state=None):
        assert isinstance(msg, Message)
        m = MessageDb()
        m.id = msg.id
        m.uid = msg.from_user.id
        m.type = msg.type
        m.text = msg.text
        m.interface = msg.interface.__class__.__name__
        m.datetime = datetime.datetime.utcnow()
        m.state = state
        m.ext = json.dumps(msg.ext)
        db_session.add(m)
        db_session.commit()

    @classmethod
    def _db_to_obj(self, db):
        interface = INTERFACE_STORE[db.interface]
        m = Message(
                db.idx,
                db.text,
                db.type,
                User.get_by_id(db.uid, interface),
                interface,
                ext=json.loads(db.ext),
                )
        m.state = db.state
        return m

    @classmethod
    def get_message(
            cls, state, msg_type=Type.TEXT, rand=True, limit=100):
        ret = []
        rand_func = MessageDb.id
        if rand:
            rand_func = func.random()

        db = MessageDb.query.filter_by(state=state, type=msg_type)\
            .order_by(rand_func)\
            .limit(limit)
        query = db.all()
        if query:
            ret = [cls._db_to_obj(q) for q in query]
        return ret


class User(object):

    log = logging.getLogger(__name__)

    def __init__(self, uid, display_name, interface, admin=False):
        self.id = uid
        self.display_name = display_name
        self.interface = interface
        self.admin = admin

    @classmethod
    def get_by_id(cls, uid, interface):
        udb = None
        try:
            udb = UserDb.query.filter_by(
                id=uid, interface=interface.__class__.__name__).first()
        except sqlalchemy.orm.exc.NoResultFound:
            pass
        if udb:
            if udb.display_name is None:
                obj = interface.get_user_profile(uid)
                udb.display_name = obj.display_name
                db_session.commit()
            return User(udb.id, udb.display_name, interface, udb.admin)
        else:
            try:
                obj = interface.get_user_profile(uid)
            except UserNotFound:
                return User(uid, 'UNKNOWN:' + uid, interface, False)
            else:
                u = UserDb()
                u.id = obj.id
                u.display_name = obj.display_name
                u.interface = obj.interface.__class__.__name__
                db_session.add(u)
                db_session.commit()
                return obj

    @classmethod
    def get_all_admin(self, interface):
        ret = []
        for udb in UserDb.query.filter_by(admin=True).all():
            u = User(udb.id, udb.display_name, interface, udb.admin)
            ret.append(u)
        return ret


class BaseInterface(six.with_metaclass(abc.ABCMeta, object)):

    def __init__(self, *argv, **kwargv):
        self.log = logging.getLogger(__name__)

    @abc.abstractmethod
    def get_msg_data(self, mid):
        pass

    @abc.abstractmethod
    def send_msg(self, user, msg):
        pass

    @abc.abstractmethod
    def recv_msg(self, raw):
        pass

    @abc.abstractmethod
    def get_user_profile(self, user):
        pass


def InterfaceFactory(name, config):
    from chatbot.interface.lineV2 import LineV2Interface
    INERTFACE_TAB = {
        'lineV2': LineV2Interface,
    }

    interface = None
    cls = INERTFACE_TAB.get(name)
    if cls:
        interface = cls(config)
        INTERFACE_STORE[cls.__name__] = interface
    else:
        raise InterfaceNotFound("interface not found %s" % name)
    return interface
