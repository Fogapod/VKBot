# coding:utf8


import random

HELP_TEXT = (
    (
        u'--Страница 1--\n\n'
        u'Версия: {version}\n\n'
        u'Обращения к боту: {appeals}\n\n'
        u'Список доступных команд:\n'
        u'-help\n'
        u'-say\n'
        u'-calculate\n'
        u'-find\n'
        u'-chance\n'
        u'-who\n'
        u'-couple\n'
        u'-weather\n'
        u'-ping\n'
        u'-ignore\n'
        u'-rex\n\n'
        u'Для получения детальной информации о команде, напишите {appeal} help <команда>\n'
        u'Разработчик бота: {author}'
    ),
    (
        u'\n--Страница 2--\n\n'
        u'-learn\n'
        u'-forgot'
    ),
    (
        u'\n--Страница 3--\n\n'
        u'-blacklist\n'
        u'-restart'
    ),
    (
        u'--Страница 4--\n\n'
        u'-stop\n'
        u'-whitelist\n'
        u'raise\n'
        u'-pause'
    )
)

#TODO: generate automaticly


class Plugin(object):
    __doc__ = '''Плагин предназначен для получения информации о других плагинах.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} <страница> или {keyword} <команда>
    Пример: {keyword} blacklist'''

    name = 'help'
    keywords = (u'помощь', name, '?')
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        if len(msg.args) > 1:
            try:
                page = int(msg.args[1])
            except ValueError:
                name = msg.args[1].lower()
                doc = None

                for plugin_name in utils.get_plugin_list():
                    plugin = utils.get_plugin(plugin_name)

                    if name in plugin.keywords:
                        doc = self.format_plugin_docstring(plugin)
                        break

                if doc is None:
                    rsp.text = u'Команда не существует или неверно указана страница'
                else:
                    rsp.text = doc

                return rsp
        else:
            page = 1

        if page == 0:
            rsp.text = '\n\n'.join(HELP_TEXT)
        elif page > 0:
            if not 0 < page <= len(HELP_TEXT):
                rsp.text = u'Такой страницы не существует'
            else:
                rsp.text = HELP_TEXT[page - 1]
        else:
            if page == -1:
                rsp.text = u'Пользовательские плагины:\n'
                rsp.text += '\n'.join(utils.get_custom_plugin_list())
            else:
                rsp.text = u'Такой страницы не существует'

        return rsp

    def format_plugin_docstring(self, p):
        if not p.__doc__:
            return u'Плагин не документирован'

        return p.__doc__.decode('utf8').format(keyword=random.choice(p.keywords),
                                               keywords=' '.join(p.keywords),
                                               protection=p.protection)