# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для поиска информации.
    Ключевые слова: [{keywords}]
    Использование: {keyword} <запроос>
    Пример: {keyword} телефон'''

    name = 'find'
    keywords = (u'найди', name)
    protection = 0
    argument_required = True

    def respond(self, msg, rsp, utils, *args, **kwargs):
        params = {
            'q': ' '.join(msg.args[1:]),
            'o': 'json'
        }

        response, error = \
            utils.vkr.http_r_get('https://api.duckduckgo.com', params=params)

        if error:
            rsp.text = u'Возникла ошибка'
            return rsp

        response_json = response.json()

        result = response_json['AbstractText']

        if not result:
            rsp.text = u'Ничего не найдено :/'
        else:
            image_url = response_json['Image']

            if image_url:
                pid = msg.chat_id if msg.from_chat else msg.user_id

                attachment_id, error = \
                    utils.vkr.attach_image(pid, image_url=image_url)

                if error:
                    rsp.text = \
                        result + u'\n\nВозникла ошибка при загрузке фото (' + \
                            image_url + ')'
                    return rsp

                rsp.attachments.append(attachment_id)
 
            rsp.text = result

        return rsp