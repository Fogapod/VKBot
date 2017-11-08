# coding:utf8


import random


class Plugin(object):
    __doc__ = '''Плагин предназначен для определения достоверности утверждения.
    Ключевые слова: [{keywords}]
    Использование: {keyword} <утверждение>
    Пример: {keyword} я написал хорошего бота'''

    name = 'chance'
    keywords = (u'инфа', name, u'%')
    protection = 0
    argument_required = True

    def respond(self, msg, rsp, *args, **kwargs):
        rsp.text = u'Вероятность ' + str(random.randrange(102)) + '%'

        return rsp