#coding:utf8


HELP_TEXT = (
    (
        u'--Страница 1--\n\n'
        u'Версия: {version}\n\n'
        u'Обращения к боту: {appeals}\n\n'
        u'Команды 0-го уровня:\n\n'
        u'-help\n'
        u'-say\n'
        u'-calculate\n'
        u'-find\n'
        u'-chance\n'
        u'-who\n'
        u'-weather\n'
        u'-ping\n'
        u'-ignore\n\n'
        u'Разработчик бота: {author}'
    ),
    (
        u'\n--Страница 2--\n\n'
        u'Команды 1-го уровня\n\n'
        u'-learn\n'
        u'-forgot'
    ),
    (
        u'\n--Страница 3--\n\n'
        u'Команды 2-го уровня\n\n'
        u'-blacklist\n'
        u'-restart'
    ),
    (
        u'--Страница 4--\n\n'
        u'Команды 3-го уровня\n\n'
        u'-stop\n'
        u'-whitelist\n'
        u'raise\n'
        u'-pause'
    )
)

#TODO: generate automaticly


class Plugin(object):
    __doc__ = '''Плагин предназначен для получения информации о других плагинах.
    Использование: помощь <страница> или помощь <команда>
    Пример: помощь blacklist'''

    name = 'help'
    keywords = (u'помощь', name, '?')
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        if len(msg.args) > 1:
            try:
                page = int(msg.args[1])
            except ValueError:
                plugin = utils.get_plugin(msg.args[1])

                if plugin is None:
                    rsp.text =  u'Неверно указана страница'
                else:
                    rsp.text = plugin.__doc__

                return rsp
        else:
            page = 1

        if page == 0:
            rsp.text = '\n\n'.join(HELP_TEXT)
        else:
            if not 0 < page <= len(HELP_TEXT):
                rsp.text = u'Такой страницы не существует'
            else:
                rsp.text = HELP_TEXT[page - 1]

        return rsp