# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для добавления себя в чёрный список.
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'ignore'
    keywords = (u'игнор', name)
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        blacklist = utils.get_blacklist()
        user_id = msg.real_user_id

        if user_id in blacklist:
            rsp.text = u'Вы уже заблокированы. Отказано'
            return rsp

        blacklist[user_id] = u'По собственному желанию'

        utils.save_blacklist(blacklist)

        rsp.text = u'id %s добавлен в чёрный список по собственному желанию' \
            % user_id

        return rsp