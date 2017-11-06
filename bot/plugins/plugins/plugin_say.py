#coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для отправки ботом определённого текста.
    Использование: скажи <текст>
    Пример: скажи привет'''

    name = 'say'
    keywords = (u'скажи', name)
    protection = 0
    argument_required = True

    def respond(self, msg, rsp, *args, **kwargs):
        rsp.text = ' '.join(msg.args[1:])

        return rsp