# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для остановки бота.
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'stop'
    keywords = (u'стоп', name, '!')
    protection = 3
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        utils.stop_bot()
        rsp.text = u'Завершаю работу. Удачного времени суток!'

        return rsp