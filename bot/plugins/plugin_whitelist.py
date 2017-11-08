# coding:utf8


import re


DEFAULT_ACCESS_LEVEL = 1


class Plugin(object):
    __doc__ = '''Плагин предназначен для выдачи повышенных прав доступа.
    Ключевые слова: [{keywords}]
    Использование: {keyword} <id>
      *Просмотр всего списка: {keyword}
    Пример: {keyword} fogapod'''

    name = 'whitelist'
    keywords = (u'вайтлист', name)
    protection = 3
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        utils.log(u'Вызов функции whitelist', 0)

        whitelist = utils.get_whitelist()

        if len(msg.args) == 1:
            if len(whitelist.keys()) == 0:
                rsp.text = u'Список пуст'
            else:
                rsp.text = ''
                for i, uid in enumerate(whitelist.keys()):
                    rsp.text += u'%d. {id%d_name} (%d) Доступ: %d\n' \
                        % (i+1, uid, uid, whitelist[uid])
                rsp.text = rsp.text[:-1]

            return rsp

        user_id = msg.args[1]

        if not re.match('\d+$', user_id):
            user_id, error = utils.vkr.get_real_user_id(user_id)
            if not user_id and '113' in error:
                rsp.text = u'Указан неверный id пользователя'
                return rsp

        user_id = int(user_id)

        if len(msg.args) == 2:
            access_level = DEFAULT_ACCESS_LEVEL
        else:
            access_level = msg.args[2]
            if not re.match('\d+$', access_level) \
                    or int(access_level) not in range(4):
                rsp.text = u'Указан неверный уровень доступа'
                return rsp
            else:
                access_level = int(access_level)

        if access_level == 0:
            if user_id in whitelist:
                whitelist.pop(user_id)
        else:
            whitelist[user_id] = access_level

        utils.save_whitelist(whitelist)

        utils.log(
            u'[b]id %s добавлен в whitelist. Доступ: %d[/b]'
            % (user_id, access_level), 2)

        rsp.text = u'Теперь {id%s_name} имеет доступ %d' \
            % (user_id, access_level)

        return rsp