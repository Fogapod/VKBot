#coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для вызова ошибки бота.
    Использование: raise <ошибка>
    Пример: raise Exception'''

    name = 'raise'
    keywords = (name, )
    protection = 3
    argument_required = False

    def respond(self, msg, rsp, *args, **kwargs):
        if len(msg.args) == 1:
            exception_text = 'Default exception text'
        else:
            exception_text = ' '.join(msg.args[1:])

        raise Exception(exception_text)