# coding:utf8


import re


class Plugin(object):
    __doc__ = '''Плагин предназначен для блокировки страниц.
    Ключевые слова: [{keywords}]
    Использование: {keyword} <+|-> <id>
      *просмотр всего списка: {keyword}
      *если не указать id, будет заблокирован/разблокирован текущий диалог
    Пример: {keyword} + fogapod'''

    name = 'blacklist'
    keywords = (u'чс', name)
    priority = 1000
    protection = 2
    argument_required = False
        
    def respond(self, msg, rsp, utils, *args, **kwargs):
        blacklist = utils.get_blacklist()

        if len(msg.args) == 1:
            if not blacklist:
                rsp.text = u'Список пуст'
            else:
                rsp.text = ''

                for i, uid in enumerate(blacklist.keys()):
                    rsp.text += u'%d. {id%d_name} (%d): %s\n' \
                                % (i + 1, uid, uid, blacklist[uid])
                rsp.text = rsp.text[:-1]
            return rsp

        else:
            if msg.args[1] == '+':
                blacklist_reason = ''

                if len(msg.args) == 2:
                    chat_id = msg.chat_id if msg.from_chat else msg.user_id
                else:
                    blacklist_reason = re.search(
                        u'.*?((причина)|(reason)):((.|\n)+)', msg.text, re.I)

                    if blacklist_reason:
                        blacklist_reason = blacklist_reason.group(4)
                        if len(msg.args) == 3:
                            chat_id = \
                                msg.chat_id if msg.from_chat else msg.user_id
                        else:
                            if msg.args[2].lower().startswith(
                                    ('reason:', u'причина')):
                                chat_id = msg.chat_id if msg.from_chat \
                                    else msg.user_id
                            else:
                                chat_id = msg.args[2]
                    else:
                        chat_id = msg.args[2]

                    if not (type(chat_id) is int or re.match('\d+$', chat_id)):
                        chat_id, error = utils.vkr.get_real_user_id(chat_id)

                        if not chat_id and '113' in error:
                            rsp.text = u'Неправильно указан id'
                            return rsp
                    else:
                        chat_id = int(chat_id)

                if not blacklist_reason:
                    blacklist_reason = u'Причина не указана'

                blacklist[chat_id] = blacklist_reason
                utils.save_blacklist(blacklist)

                utils.log(u'id %s добавлен в чёрный список по причине: %s'
                          % (chat_id, blacklist_reason), 1)

                rsp.text = u'id %s добавлен в список по причине: %s' \
                           % (chat_id, blacklist_reason)

            elif msg.args[1] == '-':
                if len(msg.args) == 2:
                    chat_id = msg.chat_id if msg.from_chat else msg.user_id
                else:
                    chat_id = msg.args[2]
                    if not re.match('-?\d+$', chat_id):
                        chat_id, error = utils.vkr.get_real_user_id(chat_id)
                        if not chat_id and '113' in error:
                            rsp.text = u'Неправильно указан id'
                            return rsp
                    else:
                        chat_id = int(chat_id)

                if chat_id not in blacklist:
                    rsp.text = u'В списке нет данного id'
                    return rsp

                blacklist.pop(chat_id)
                utils.save_blacklist(blacklist)

                utils.log(u'id %s удалён из чёрного списка' % chat_id, 1)
                rsp.text = u'id %s удалён из списка' % chat_id

            else:
                rsp.text = u'Неизвестная опция'

        return rsp