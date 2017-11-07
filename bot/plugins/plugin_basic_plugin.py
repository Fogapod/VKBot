#coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для
    Использование: 
    Пример: '''

    disabled = True

    name = 'plugin'
    keywords = (u'плагин', name)
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, *args, **kwargs):
        rsp.text = u'Ответ от плагина'

        return rsp