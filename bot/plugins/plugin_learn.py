# coding:utf8


RESPONSE_FORM = (
    u'Команда выучена.'
    u'Теперь на «{}» я буду отвечать «{}»\n\n'
    u'Опции:\n' # TODO: more readable output
    u'use_regex: {}\n'
    u'force_unmark: {}\n'
    u'force_forward: {}\n'
    u'appeal_only: {}\n'
    u'disabled: {}\n'
)


class Plugin(object):
    __doc__ = '''Плагин предназначен для добавления команд.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} команда::Ответ::опции
    Пример: {keyword} привет::Здравствуй::02120'''

    name = 'learn'
    keywords = (u'выучи', name, '+')
    priority = 750
    protection = 1
    argument_required = True

    def respond(self, msg, rsp, utils, *args, **kwargs):
        custom_commands = utils.get_custom_commands()

        if custom_commands is None:
            rsp.text = u'Пользовательские команды отключены или повреждены'
            return rsp

        text = ' '.join(msg.args[1:])

        if '::' in text:
            text = text.split('::')
            command  = text[0]
            response = text[1]

            if len(text) == 3 and text[2]:
                try:
                    options = map(lambda x: int(x), text[2])
                except:
                    rsp.text =  u'Ошибка при разборе опций'
                    return rsp
            else:
                options = [0, 0, 0, 0, 0]

            if options[0] == 0:
                command = command.lower()
        else:
            text = ''

        if len(text) < 2 or not command:
            rsp.text = u'Неправильный синтаксис команды'
        elif len(options) != 5:
            rsp.text = u'Неправильное количество опций'
        elif command in custom_commands.keys() \
                and response in custom_commands[command]:
            rsp.text = u'Я уже знаю такой ответ'
        elif command in custom_commands:
            # update regex option for all responses
            for r in custom_commands[command]:
                r[1] = options[0] if options[0] in (0, 2) else 0

            custom_commands[command].append([response] + options)
            rsp.text = RESPONSE_FORM.format(command, response, *options)
        else:
            custom_commands[command] = [[response] + options]
            rsp.text = RESPONSE_FORM.format(command, response, *options)

        utils.log(u'Пользовательские команды сохраняются...', 0)
        utils.save_custom_commands(custom_commands)
        utils.log(u'Пользовательские команды сохранены', 1)

        return rsp