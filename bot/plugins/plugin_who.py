#coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для выбора участника беседы 
    Использование: кто <вопрос>
    Пример: кто съел арбуз?'''

    name = 'who'
    keywords = (u'кто', name)
    protection = 0
    argument_required = True

    def respond(self, msg, rsp, utils, *args, **kwargs):
        if not msg.from_chat:
            rsp.text = u'Данная команда работает только в беседе'
        elif len(msg.chat_users) < 2:
            rsp.text = u'Для корректной работы команды, в беседе должно наход' \
                       u'иться больше одного человека'
        else:
            user_name, error = utils.vkr.get_name_by_id(
                object_id=msg.random_chat_user_id, name_case='acc')

            if user_name:
                rsp.text = u'Я выбираю [id%d|%s]' \
                    % (msg.random_chat_user_id, user_name)
            else:
                rsp.text = u'Произошла ошбка'

        return rsp