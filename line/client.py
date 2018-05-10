import logging
import requests
try:
    from urlparse import urlparse, urljoin
except:
    from urllib.parse import urlparse, urljoin


class Client(object):

    BASE_URL = 'https://api.line.me/v2/bot'

    def __init__(self, channel_access_token):
        self.log = logging.getLogger(__name__)
        self.channel_access_token = channel_access_token

    def _gen_url(self, *paths):
        parsed_url = urlparse(self.BASE_URL)
        path = parsed_url.path.split('/')
        path.extend(paths)
        path = '/'.join(path)
        return urljoin(parsed_url.geturl(), path)

    def _gen_header(self):
        return {'Authorization': 'Bearer %s' % self.channel_access_token}

    def _get(self, url):
        return requests.get(url, headers=self._gen_header())

    def _post(self, url, data):
        return requests.post(
            url,
            headers=self._gen_header(),
            json=data)

    def send_msg(self, uid, messages):
        messages = messages if type(messages) is list else [messages]

        url = self._gen_url('message', 'push')
        data = {
            'to': uid,
            "messages": [m.pack() for m in messages]
        }
        return self._post(url, data)

    def reply_msg(self, reply_token, messages):
        messages = messages if type(messages) is list else [messages]

        url = self._gen_url('message', 'reply')
        data = {
            'replyToken': reply_token,
            'messages': [m.pack() for m in messages],
        }
        print(data)
        return self._post(url, data)

    def get_content(self, content_id):
        url = self._gen_url('message', content_id, 'content')
        return self._get(url)

    def get_profile(self, uid):
        url = self._gen_url('profile', uid)
        return self._get(url)
