# coding:utf8


import copy


class Plugin(object):
    __doc__ = '''Плагин предназначен для перезагрузки бота (применение настроек).
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'restart'
    keywords = (u'перезапуск', name)
    protection = 2
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        startup_response = copy.deepcopy(rsp)
        startup_response.text = u'Перезагрузка завершена'
        utils.set_startup_response(startup_response)

        utils.restart_bot()
        rsp.text = u'Начинаю перезагрузку'

        return rsp