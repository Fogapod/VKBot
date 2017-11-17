# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для отправки ботом определённого текста.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} <текст>
    Пример: {keyword} привет'''

    name = 'say'
    keywords = (u'скажи', name)
    protection = 0
    argument_required = True

    def respond(self, msg, rsp, *args, **kwargs):
        rsp.text = ' '.join(msg.args[1:])

        return rsp