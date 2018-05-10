import six
import yaml
import logging
import sqlalchemy
from flask import Flask
from flask import request
from flask_restful import Resource
from flask_restful import Api
from flask_restful import reqparse
from chatbot.interface import InterfaceFactory
from chatbot.interface import Message
from chatbot.model import do_init as init_model
from chatbot.model import db_session
from chatbot.model.user import User as UserDb
from chatbot.handler import Handler


def setup_log():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    root.addHandler(console)


def init_interface(config):
    ret = {}
    for name, info in six.iteritems(config):
        interface = InterfaceFactory(name, info['config'])
        ret[name] = interface

        # init admin
        for uid in info.get('admin', []):
            udb = None
            try:
                udb = UserDb.query.filter_by(
                    id=uid, interface=interface.__class__.__name__).first()
            except sqlalchemy.orm.exc.NoResultFound:
                pass
            if udb is None:
                udb = UserDb()
                udb.id = uid
                udb.interface = interface.__class__.__name__
                db_session.add(udb)
            udb.admin = True
            db_session.commit()
    return ret


# class LineMsgCallback(Resource):
#
#     def post(self):
#         data = request.get_json(force=True)
#         print(data)


def gen_callback(fn):
    class callback_wrap(Resource):
        def post(self):
            data = request.get_json(force=True)
            handler = Handler()
            for m in fn.recv_msg(data):
                handler.add(m)
    callback_wrap.__name__ = fn.__class__.__name__
    return callback_wrap


class RandonMessage(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=int)
        parser.add_argument('rand', type=int)
        parser.add_argument('limit', type=int)
        args = parser.parse_args()
        print(args)
        msg_type = args.type if args.type else Message.Type.TEXT
        rand = False if (args.rand == 0) else True
        limit = args.limit if args.limit else 100
        ret = []
        mlist = Message.get_message(
            Handler.Mode.PARTY, rand=rand, limit=limit, msg_type=msg_type)
        for m in mlist:
            tmp = {
                'user': m.from_user.display_name,
                'data': m.text,
                'type': m.type,
            }
            ret.append(tmp)
        return ret


if __name__ == '__main__':

    setup_log()
    init_model()

    with open('config.yml', 'r') as fd:
        config = yaml.load(fd)

    interface_info = init_interface(config['interface'])

    app = Flask(__name__)
    api = Api(app)
    api.add_resource(RandonMessage, '/api/msg')
    # api.add_resource(LineMsgCallback, '/api/line_msg_callback')
    for name, info in six.iteritems(config['interface']):
        api.add_resource(gen_callback(interface_info[name]), info['url'])

    app.run(debug=True, host='0.0.0.0')
