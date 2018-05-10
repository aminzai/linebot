import six
import abc


class Message(six.with_metaclass(abc.ABCMeta, object)):

    def __init__(self, channel=None):
        self.channel = channel

    @abc.abstractmethod
    def pack(self):
        pass


class TextMessage(object):

    def __init__(self, text, *argv, **kwargv):
        super(TextMessage, self).__init__(*argv, **kwargv)
        self.text = text

    def pack(self):
        return {'type': 'text', 'text': self.text}


class StickerMessage(object):

    def __init__(self, package_id, sticker_id, *argv, **kwargv):
        super(StickerMessage, self).__init__(*argv, **kwargv)
        self.package_id = package_id
        self.sticker_id = sticker_id

    def pack(self):
        return {
                'type': 'sticker',
                'packageId': self.package_id,
                'stickerId': self.sticker_id,
                }


class ImageMessage(object):

    def __init__(self, path, preview, *argv, **kwargv):
        super(ImageMessage, self).__init__(*argv, **kwargv)
        self.path = path
        self.preview = preview

    def pack(self):
        return {
                'type': 'image',
                'originalContentUrl': self.path,
                'previewImageUrl': self.path,
                }
