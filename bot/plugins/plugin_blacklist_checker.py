#coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для блокирования команд, если пользователь/диалог заблокирован
    Использование: -
    Пример: -'''

    name = 'blacklist_checker'
    keywords = (name)
    priority = 999
    protection = 0
    argument_required = False

    def _accept_request(self, msg, rsp, utils, *args, **kwargs):
        blacklist = utils.get_blacklist()

        return msg.real_user_id in blacklist or msg.chat_id in blacklist

    def respond(self, msg, rsp, args, **kwargs):
        rsp.text = 'pass'

        return rsp