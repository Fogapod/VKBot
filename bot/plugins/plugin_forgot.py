# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для удаления команд.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} команда::Ответ
    Пример: {keyword} привет::Пока'''

    name = 'forgot'
    keywords = (u'забудь', name, '-')
    priority = 750
    protection = 1
    argument_required = True

    def respond(self, msg, rsp, utils, *args, **kwargs):
        custom_commands = utils.get_custom_commands()

        if custom_commands is None:
            rsp.text = u'Пользовательские команды отключены или повреждены'
            return rsp

        response_text = u'Команда забыта'

        text = ' '.join(msg.args[1:])

        if '::' in text:
            text = text.split('::')
            command  = text[0]
            response = text[1]
        else:
            command  = text
            response = None

        if response is not None:
            if command not in custom_commands:
                rsp.text = u'Я не знаю такой команды (%s)' % command
                return rsp

            elif len([x for x in custom_commands[command]
                     if response == x[0]]) == 0:
                rsp.text = u'В команде «%s» нет ключа «%s»' % (command, response)
                return rsp

            else:
                for response_list in custom_commands[command]:
                    if response_list[0] == response:
                        custom_commands[command].remove(response_list)
                        break
                if len(custom_commands[command]) == 0:
                    custom_commands.pop(command)
                else:
                    response_text = u'Ключ для команды забыт'

        else:
            if custom_commands.pop(command, None) is None:
                rsp.text = u'Я не знаю такой команды (%s)' % command
                return rsp

        utils.log(u'Пользовательские команды сохраняются...', 0)
        utils.save_custom_commands(custom_commands)
        utils.log(u'Пользовательские команды сохранены', 1)

        rsp.text = response_text

        return rsp