# coding:utf8


import time


class Plugin(object):
    __doc__ = """Плагин предназначен для получения информации о погоде.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} <?город>
    Пример: {keyword} Ufa"""

    name = 'weather'
    keywords = (u'погода', name)
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        api_key = utils.get_settings('openweathermap_api_key')

        if api_key is None:
            api_key = '0'
            utils.save_setting('openweathermap_api_key', api_key)

        if len(msg.args) > 1:
            if ' '.join(msg.args[1:]) == '-':
                utils.save_setting('openweathermap_api_key', '0')
                rsp.text =  u'Ключ сброшен'

                return rsp

            if api_key == '0':
                if self.verify_openweathermap_api_key(msg, utils):
                    utils.save_setting('openweathermap_api_key', msg.args[1])
                    rsp.text = u'Ключ подтверждён'
                else:
                    rsp.text = u'Неверный ключ (%s)' % msg.args[1]

                return rsp

            city = ' '.join(msg.args[1:])
        else:
            if api_key == '0':
                rsp.text = (
                    u'Команда не может функционировать. Для её активации '
                    U'необходим специальный ключ:\n'
                    u'https://github.com/Fogapod/VKBot/blob/master/README.md#openweathermap\n'
                    u'Скопируйте полученный ключ и повторите команду, добавив'
                    U' его, чтобы получилось\n'
                    u'/погода 9ld10763q10b2cc882a4a10fg90fc974\n\n'
                    u'[id{my_id}|НИКОМУ НЕ ПОКАЗЫВАЙТЕ ДАННЫЙ КЛЮЧ, ИНАЧЕ РИСКУЕТЕ ЕГО ПОТЕРЯТЬ!]'
                )

                return rsp

            city, error = utils.vkr.execute('''
                var user;
                user = API.users.get({"user_ids": "%d", "fields": "city"})[0];
                return user["city"]["title"];
            ''' % msg.real_user_id)

            if not city:
                city = 'Moscow'

        params = {
            'APPID': api_key,
            'q': city,
            'lang': 'ru',
            'units': 'metric'
        }

        weather_data, error = \
            utils.vkr.http_r_get(
                'https://api.openweathermap.org/data/2.5/weather', params=params
            )

        if error:
            rsp.text =  u'Возникла ошибка'

            return rsp

        weather_json = weather_data.json()

        if 'cod' in weather_json and weather_json['cod'] == '404':
            rsp.text = u'Город не найден (%s)' % city

            return rsp

        format_dict = {}
        format_dict['city']    = city
        format_dict['country'] = weather_json['sys']['country']
        format_dict.update(weather_json['main'])
        format_dict.update(weather_json['weather'][0])
        format_dict['temp']  = round(format_dict['temp'], 1)
        format_dict['temp']  = format_dict['temp']
        format_dict['cloud'] = weather_json['clouds']['all']
        format_dict['time_since_calculation'] = time.strftime(
            '%H:%M:%S', time.gmtime(time.time() - weather_json['dt'])
        )

        weather_response = (
            u'Погода для: {city} ({country})\n\n'
            u'Состояние погоды: {description}\n'
            u'Температура: {temp}°C\n'
            u'Облачность: {cloud}%\n'
            u'Влажность: {humidity}%\n'
            u'Давление: {pressure} hPa\n'
            u'Прошло с момента последнего измерения: {time_since_calculation}'
        ).format(**format_dict)

        rsp.text = weather_response

        return rsp

    def verify_openweathermap_api_key(self, msg, utils):
        api_key = msg.args[1]

        test_url = 'https://api.openweathermap.org/data/2.5/weather?APPID=%s' \
            % api_key
        response, error = utils.vkr.http_r_get(test_url)

        if error:
            return False

        test_weather_json = response.json()

        if 'cod' in test_weather_json:
            if test_weather_json['cod'] == '401':
                return False
            elif test_weather_json['cod'] == '400':
                return True
