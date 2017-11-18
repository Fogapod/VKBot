# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для ответа в случае, если ни одна из команд не была вызвана, но было обращение.
    Ключевые слова: -
    Использование: -
    Пример: -'''

    name = 'unknown_command'
    keywords = (name)
    priority = -1000
    protection = 0
    argument_required = False

    def _accept_request(self, msg, *args, **kwargs):
        return msg.was_appeal

    def respond(self, msg, rsp, args, **kwargs):
        rsp.text = u'Неизвестная команда. Вы можете использовать {appeal} ' \
                   u'help для получения списка команд.'

        return rsp