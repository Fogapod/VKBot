# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для приостановки работы бота (игнорирование сообщений).
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} <секунды>
    Пример: {keyword} 60'''

    name = 'pause'
    keywords = (u'пауза', name)
    protection = 3
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        if len(msg.args) == 2:
            try:
                delay = float(msg.args[1])
            except ValueError:
                rsp.text = u'Неправильный аргумент'
                return rsp
        else:
            delay = 5

        utils.log(u'Начало паузы длиной в (%s) секунд' % delay, 1)
        time.sleep(delay)
        utils.log(u'Окончание паузы длиной в (%s) секунд' % delay, 1)

        utils.clear_message_queue()

        rsp.text = u'Пауза окончена'

        return rsp