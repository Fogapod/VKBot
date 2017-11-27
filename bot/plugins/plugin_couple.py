# coding:utf8


import random


class Plugin(object):
    __doc__ = '''Плагин предназначен для выбора пары человек в беседе.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'couple'
    keywords = (name, u'пара', u'парочка')
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        if not msg.from_chat:
            rsp.text = u'Данная команда работает только в беседе'
        elif len(msg.chat_users) < 2:
            rsp.text = u'Для корректной работы команды, в беседе должно наход' \
                       u'иться больше одного человека'
        else:
            uid1, uid2 = random.sample(msg.chat_users, 2)

            response, error = utils.vkr.execute('''
                var users = API.users.get({"user_ids": [%d, %d]});
                var name1 = users[0].first_name + " " + users[0].last_name;
                var name2 = users[1].first_name + " " + users[1].last_name;
                return [name1, name2];
            ''' % (uid1, uid2))

            name1, name2 = response

            if name1 and name2:
                rsp.text = u'Я думаю, это [id%d|%s] и [id%d|%s]' % \
                    (uid1, name1, uid2, name2)
            else:
                rsp.text = u'Произошла ошбка'

        return rsp