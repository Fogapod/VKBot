#coding:utf8

import time


class Plugin(object):
    __doc__ = '''Плагин предназначен для проверки времени ответа бота.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'ping'
    keywords = (u'пинг', name)
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, *args, **kwargs):
        delta = int(round((time.time() - msg.date) * 1000))
        rsp.forward_id = 0
        rsp.text = u'pong, заняло ' + str(delta) + u'мс'

        return rsp