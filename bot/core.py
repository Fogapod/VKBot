# coding:utf8


import time
import re
import math
import random

from threading import Thread

import requests as r

from utils import TOKEN_FILE_PATH, load_custom_commands,\
save_custom_commands, load_blacklist, save_blacklist,\
CUSTOM_COMMAND_OPTIONS_COUNT

import vkrequests as vkr

__version__ = '0.1.0dev'
AUTHOR_VK_ID = 180850898
__author__ = 'Eugene Ershov - https://vk.com/id%d' % AUTHOR_VK_ID

__help__ = (
u'''
--Страница 0--
Версия: {version}

Обращения к боту: {appeals}

Базовые команды:
-Показывать это сообщение (?)
(помощь|help) <?страница=0>
-Написать сообщение
(скажи|say) <фраза>
-Посчитать математическое выражение (=)
(посчитай|calculate) <выражение>
-Проверить, простое ли число (%)
(простое|prime) <число>
-Определить достоверность информации
(инфа|chance) <вопрос>
-Выбрать участника беседы
(кто|who) <вопрос>
-Сообщить информацию о погоде
погода|weather <?город=город со страницы или Москва>|-

Автор: {author}
''',

u'''
--Страница 1--

Опциональные команды (доступ ограничивает владелец бота):
-Выучить команду (+)
(выучи|learn) <команда>::<ответ>::<?опции=00000>
-Забыть команду (-)
(забудь|forgot) <команда>::<?ответ>''',

u'''
--Страница 2--

Ограниченные команды (доступны только владельцу):
-Игнорировать пользователя (лс), беседу или группу
blacklist <?me> <?-> <?id=id_диалога>
-Перезапустить бота (применение команд и настроек)
restart
-Выключить бота (!)
stop''',

u'''
--Страница 3--

Отладочные команды (доступны только владельцу):

-Спровоцировать ошибку бота
raise <?сообщение=Default exception text>
-Поставить бота на паузу (игнорирование сообщений)
pause <время (секунды)=5>
-Быстрая проверка активности бота (доступна всем)
ping''',
u'''
--Страница 4--

Закрытые команды (доступны только автору):
-Активировать бота
activate
-Деактивировать бота
deactivate'''
)


def safe_format(s, *args, **kwargs):
    '''
    https://stackoverflow.com/questions/9955715/python-missing-arguments-in-string-formatting-lazy-eval
    '''

    while True:
        try:
            return s.format(*args, **kwargs)
        except KeyError as e:
            e=e.args[0]
            kwargs[e] = '{%s}' % e
        except:
            return s


class Bot(object):
    '''
    This class contains 'modules' for built-in commands
    '''

    def blacklist(self, cmd, blacklist):
        if not cmd.out and not (len(cmd.words) == 2 and cmd.words[1] == 'me'):
            return u'Отказано в доступе', blacklist

        if len(cmd.words) == 1:
            chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id

            if chat_id in blacklist:
                return u'Данный id уже находится в списке', blacklist

            blacklist.append(chat_id)
            save_blacklist(blacklist)

            return u'id %s добавлен в список' % chat_id, blacklist

        else:
            if cmd.words[1] == '-':
                if len(cmd.words) == 2:
                    chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
                else:
                    if not re.match('\d+$', cmd.words[2]):
                        return u'Неправильно указан id', blacklist

                    chat_id = int(cmd.words[2])

                if chat_id not in blacklist:
                    return u'В списке нет данного id', blacklist

                blacklist.remove(chat_id)
                save_blacklist(blacklist)

                return u'id %s удалён из списка' % chat_id, blacklist

            elif cmd.words[1] == 'me':
                user_id = cmd.user_id
                if user_id in blacklist:
                    return u'Данный id уже находится в списке', blacklist

                blacklist.append(user_id)
                save_blacklist(blacklist)

                return u'id %s добавлен в список' % user_id, blacklist

            else:
                if not re.match('\d+$', cmd.words[1]):
                    return u'Неправильно указан id', blacklist

                chat_id = int(cmd.words[1])

                if chat_id in blacklist:
                    return u'Данный id уже находится в списке', blacklist

                blacklist.append(chat_id)
                save_blacklist(blacklist)

                return u'id %s добавлен в список' % chat_id, blacklist

    def pong(self, cmd):
        cmd.forward_msg = None
        return 'pong', cmd

    def help(self, cmd):
        if len(cmd.words) > 1:
            try:
                page = int(cmd.words[1])
            except ValueError:
                return u'Неверно указана страница'
        else:
            page = 0

        if page == -1:
            response_text = '\n'.join(__help__)
        else:
            try:
                response_text = __help__[page]
            except IndexError:
                return u'Такой страницы не существует'

        return response_text

    def say(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        text = ' '.join(words)
        return text        

    def calculate(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

        if words[0].startswith('='):
            words[0] = words[0][1:]
        else:
            del words[0]
        words = ''.join(words).lower()
        if re.match(u'^([\d+\-*/%:().,^√πe]|(sqrt)|(pi))+$', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π', 'math.pi', words)
            words = re.sub('e', 'math.e', words)
            words = re.sub('\^', '**', words)
            words = re.sub(',', '.', words)
            words = re.sub(u':|÷', '/', words)
            while True:
                if '/' in words:
                    index = re.search('[^.\d]\d+[^.\de]', words)
                    if index:
                        index = index.end() - 1
                        words = words[:index] + '.' + words[index:]
                    else:
                        break
                else:
                    break
            try:
                result = eval(words)
            except SyntaxError:
                result = u'Ошибка [0]'
            except NameError:
                result = u'Ошибка [1]'
            except AttributeError:
                result = u'Ошибка [2]'
            except TypeError:
                result = u'Ошибка [3]'
            except ZeroDivisionError:
                result = u'Деление на 0'
            except OverflowError:
                result = 'Infinite'
            else:
                if type(result) not in (int, long, float):
                    result = u'Не математическая операция'
                else:
                    result = str(result)
        else:
            result = u'Не математическая операция'

        return result

    def prime(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        input_number = ''.join(words)
        if re.match('^\d+$', input_number) and len(input_number)<=5:
            input_number = int(input_number)
            luc_number = 0
            last_luc_number = 0
            for i in range(input_number):
                if luc_number == 0:
                    luc_number = 1
                elif luc_number == 1:
                    last_luc_number = luc_number
                    luc_number = 3
                else:
                    luc_number, last_luc_number = last_luc_number\
                                                  + luc_number, luc_number
                            
            if input_number != 0:
                is_prime = True if (luc_number - 1) \
                                % input_number == 0 else False
                result = u'Является простым числом' \
                    if is_prime else u'Не является простым числом'
            else:
                result = u'0 не является простым числом'
        else:
            result = u'Дано неверное или слишком большое значение'
        return result

    def chance(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required

        return u'Вероятность ' + str(random.randrange(102)) + '%'

    def who(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required

        if not cmd.from_chat:
            return u'Данная команда работает только в беседе'
        elif len(cmd.chat_users) < 2:
            return u'Для корректной работы команды, в беседе должно находить' \
                   u'ся больше одного человека'
        else:
            user_name, error = vkr.get_user_name(
                user_id=cmd.random_chat_user_id, name_case='acc')
            if user_name:
                return u'Я выбираю [id%d|%s]' % (cmd.random_chat_user_id, user_name)

    def weather(self, cmd, api_key):
        api_key_not_confirmed = \
u'''
Команда не может функционировать. Для её активации необходим специальный ключ:
ИНСТРУКЦИЯ_ПО_ПОЛУЧЕНИЮ_КЛЮЧА

Скопируйте полученный ключ и повторите команду, добавив его, чтобы получилось
/погода 9ld10763q10b2cc882a4a10fg90fc974

[id{my_id}|НИКОМУ НЕ ПОКАЗЫВАЙТЕ ДАННЫЙ КЛЮЧ, ИНАЧЕ РИСКУЕТЕ ЕГО ПОТЕРЯТЬ!]'''

        if len(cmd.words) > 1:
            if ' '.join(cmd.words[1:]) == '-':
                return u'Ключ сброшен', '0'

            if api_key == '0':
                if self._verify_openweathermap_api_key(cmd):
                    return u'Ключ подтверждён', cmd.words[1]
                else:
                    return u'Неверный ключ (%s)' % cmd.words[1], api_key

            city = ' '.join(cmd.words[1:])
        else:
            if api_key == '0':
                return api_key_not_confirmed, api_key

            city, error = vkr.get_user_city(user_id=cmd.user_id)
            if not city:
                city = u'Москва'

        url = u'http://api.openweathermap.org/data/2.5/weather?APPID={api_key}&lang=ru&q={city}&units=metric'
        url = url.format(api_key=api_key, city=city)

        weather_data = r.get(url)
        weather_json = weather_data.json()

        if 'cod' in weather_json and weather_json['cod'] == '404':
            return u'Город не найден (%s)' % city, api_key

        format_dict = {}
        format_dict['city'] = city
        format_dict['country'] = weather_json['sys']['country']
        format_dict.update(weather_json['main'])
        format_dict.update(weather_json['weather'][0])
        format_dict['temp'] = round(format_dict['temp'], 1)
        format_dict['temp'] = format_dict['temp']
        format_dict['cloud'] = weather_json['clouds']['all']
        format_dict['time_since_calculation'] = time.strftime(
            '%H:%M:%S', time.gmtime(time.time() - weather_json['dt'])
        )

        weather_response = \
u'''
Погода для: {city} ({country})

Состояние погоды: {description}
Температура: {temp}°C
Облачность: {cloud}%
Влажность: {humidity}%
Давление: {pressure} hPa
Прошло с момента последнего измерения: {time_since_calculation}'''.format(
    **format_dict)

        return weather_response, api_key

    def _verify_openweathermap_api_key(self, cmd):
        api_key = cmd.words[1]

        test_url = 'http://api.openweathermap.org/data/2.5/weather?APPID=%s' % api_key
        test_weather_json = r.get(test_url).json()

        if 'cod' in test_weather_json:
            if test_weather_json['cod'] == '401':
                return False
            elif test_weather_json['cod'] == '400':
                return True

    def pause(self, cmd):
        if not cmd.out:
            return u'Отказано в доступе'

        if len(cmd.words) == 2:
            if re.match('\d+(\.\d+)?$', cmd.words[1]):
                delay = float(cmd.words[1])
            else:
                return u'Неправильный аргумент'
        else:
            delay = 5
        time.sleep(delay)

        return u'Пауза окончена'

    def learn(self, cmd, custom_commands, protect=True):
        if protect:
            if not cmd.out:
                return custom_commands, u'Отказано в доступе'

        if custom_commands is None:
            return custom_commands, u'Пользовательские команды отключены или повреждены'

        response_text = \
u'''Команда выучена.
Теперь на «{}» я буду отвечать «{}»

Опции:
use_regex: {}
force_unmark: {}
force_forward: {}
appeal_only: {}
disabled: {}'''

        words = cmd.words
        argument_required = self._is_argument_missing(words)

        del words[0]
        text = ' '.join(words)
        if '::' in text:
            text = text.split('::')
            command = text[0]
            response = text[1]
            if len(text) == 3 and text[2]:
                try:
                    options = map(lambda x: int(x), text[2])
                except:
                    return custom_commands, u'Ошибка при разборе опций'
            else:
                options = [0, 0, 0, 0, 0]

            if options[0] == 0:
                command = command.lower()
        else:
            text = ''

        if argument_required:
            response_text = argument_required
        elif len(text) < 2 or not (command and response):
            response_text = u'Неправильный синтаксис команды' 
        elif len(options) != CUSTOM_COMMAND_OPTIONS_COUNT:
            response_text = u'Неправильное количество опций'
        elif command in custom_commands.keys() and response \
                in custom_commands[command]:
            response_text = u'Я уже знаю такой ответ'
        elif command in custom_commands.keys():
            updated_commands = []

            if options[0] == 2: # use_regex
                for r in custom_commands[command]:
                    r[1] = 2
                    updated_commands.append(r)
            else:
                for r in custom_commands[command]:
                    r[1] = 0
                    updated_commands.append(r)

            custom_commands[command] = updated_commands

            custom_commands[command].append([response] + options)
            response_text = response_text.format(command, response, *options)
        else:
            custom_commands[command] = [[response] + options]
            response_text = response_text.format(command, response, *options)

        save_custom_commands(custom_commands)
        return custom_commands, response_text

    def forgot(self, cmd, custom_commands, protect=True):
        if protect:
            if not cmd.out:
                return custom_commands, u'Отказано в доступе'

        if custom_commands is None:
            return custom_commands, u'Пользовательские команды отключены или повреждены'

        response_text = u'Команда забыта'
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return custom_commands, argument_required        

        del words[0]
        text = ' '.join(words)
        if '::' in text:
            text = text.split('::')
            command = text[0]
            response = text[1]
        else:
            command = text
            response = ''

        if command and response:
            if not command in custom_commands.keys():
                response = ''
            elif len([x for x in custom_commands[command]\
                    if response == x[0]]) == 0:
                response_text = u'В команде «%s» нет ключа «%s»' \
                                            % command.lower(), response
            else:
                for response_list in custom_commands[command.lower()]:
                    if response_list[0] == response:
                        custom_commands[command].remove(response_list)
                        break
                if len(custom_commands[command]) == 0:
                    custom_commands.pop(command)
                else:
                    response_text = u'Ключ для команды забыт'

        if not response and not custom_commands.pop(command, None):
            response_text = u'Я не знаю такой команды (%s)' % command
        
        save_custom_commands(custom_commands)
        return custom_commands, response_text

    def custom_command(self, cmd, custom_commands):
        response_text = ''
        attachments = []

        if not custom_commands:
            return response_text, attachments, cmd

        response = ''
        for key in random.sample(custom_commands.keys(), \
        	       len(custom_commands.keys())):
            if custom_commands[key][0][1] == 2: # use regex
                pattern = re.compile(key, re.U + re.I)
                if pattern.search(cmd.text):
                    for resp in random.sample(custom_commands[key], \
                            len(custom_commands[key])):
                        if resp[5] == 2:
                            continue
                        else:
                            choice = resp
                            response = choice[0]
                    if response:
                        groups = pattern.findall(cmd.text)
                        groupdict = pattern.search(cmd.text).groupdict()
                        response = safe_format(response, *groups, **groupdict)
                        break

            elif cmd.text.lower() == key:
                for resp in random.sample(custom_commands[key], \
                        len(custom_commands[key])):
                    if resp[5] == 2:
                        continue
                    else:
                        choice = resp
                        response = choice[0]
                if response:
                    break

        if not response:
            return response_text, attachments, cmd

        if choice[4] == 1: # works only WITHOUT appeal
            if cmd.was_appeal:
                return response_text, attachments, cmd
        elif choice[4] == 2: # works only WITH appeal
            if not cmd.was_appeal:
                return response_text, attachments, cmd

        if choice[3] == 2: # force forward
            cmd.forward_msg = cmd.msg_id
        elif choice[3] == 1: # never forward
            cmd.forward_msg = None
            
        if choice[2] == 1: # always mark message
            cmd.mark_msg = True
        elif choice[2] == 2: # never mark message
            cmd.mark_msg = False

        if response.startswith('self='):
            cmd.text = '_' + response[5:]
            return self.custom_command(cmd, custom_commands)

        elif response.startswith('attach='):
            media_id = response[7:]
            if re.match('.*((photo)|(album)|(video)|(audio)|(doc)|(wall)|'
                            '(market))-?\d+_\d+(_\d+)?$', media_id):
                if re.match('.*album\d+_\d+', media_id):
                    album_id = re.search('album\d+_(\d+)', media_id).group(1)
                    album_len = vkr.get_album_size(album_id)[0]
                    if album_len == 0:
                        response_text = \
                            u'Пустой альбом. Невозможно выбрать фото'
                        media_id = ''
                    else:
                        media_id = vkr.get_photo_id(
                                            album_id=album_id,
                                            offset=random.randrange(album_len)
                                            )[0]
                else:
                    media_id = media_id.split('/')[-1] # URGLY # FIXME
                if media_id:
                    attachments.append(media_id)
            else:
                response_text = \
                    u'Не могу показать вложение. Неправильная ссылка'
        elif response == 'pass':
            pass
        else:
            response_text = response

        return response_text, attachments, cmd

    def activate_bot(self, cmd, activated):
        if activated:
            return u'Бот уже активирован', True
        elif cmd.from_chat and cmd.user_id == AUTHOR_VK_ID:
            return u'Активация прошла успешно', True
        else:
            return u'Отказано в доступе', False

    def deactivate_bot(self, cmd, activated):
        if cmd.from_chat and cmd.user_id == AUTHOR_VK_ID:
            return u'Деактивация прошла успешно', False
        elif activated:
            return u'Отказано в доступе', True
        else:
            return u'Отказано в доступе', False

    def _is_argument_missing(self, words):
        if len(words) == 1:
            return u'Команду необходимо использовать с аргументом'
        else:
            return False


class Command(object):
    def __init__(self, SELF_ID, appeals):
        self.SELF_ID = SELF_ID
        self.appeals = appeals
        self.raw_text = ''
        self.text = ''
        self.lower_text = ''
        self.words = ['']
        self.was_appeal = False
        self.mark_msg = True
        self.from_user = False
        self.from_chat = False
        self.from_group = False
        self.forward_msg = None
        self.user_id = 0
        self.chat_id = 0
        self.chat_users = []
        self.random_chat_user_id = 0
        self.chat_name = ''
        self.out = False
        self.event = None
        self.event_user_id = 0
        self.msg_id = 0

    def load(self, message):
        self.__init__(self.SELF_ID, self.appeals) # refresh params

        self.raw_text = message['body']
        self.text = self.raw_text
        self.lower_text = self.text.lower()

        if self.lower_text.startswith(self.appeals):
            self.text = self.text[len(next(
                a for a in self.appeals if self.lower_text.startswith(a)
            )):]
            if self.text.startswith(' '):
                self.text = self.text[1:]
            self.was_appeal = True
            if self.text.startswith('/'):
                self.text = self.text[1:]
                self.mark_msg = False

        if self.text:
            self.words = self.text.split(' ')
        self.lower_text = self.text.lower()

        self.msg_id = message['id']
        self.user_id = message['user_id']

        if self.user_id == self.SELF_ID:
            self.out = 1
        else:
            self.out = message['out']

        if 'chat_id' in message.keys():
            self.from_chat = True
        elif self.user_id < 1:
            self.from_group = True
        else:
            self.from_user = True

        if self.from_chat:
            self.chat_id = message['chat_id'] + 2000000000
            self.forward_msg = self.msg_id
            self.chat_users = message['chat_active']
            if self.chat_users:
                self.random_chat_user_id = random.choice(self.chat_users)
            self.chat_name = message['title']

            if not self.raw_text:
                self.event = message.get('action')
                if self.event:
                    if self.event == 'chat_photo_update':
                        self.event = 'photo updated'
                    elif self.event == 'chat_photo_remove':
                        self.event = 'photo removed'
                    elif self.event == 'chat_create':
                        self.event = 'chat created'
                    elif self.event == 'chat_title_update':
                        self.event = 'title updated'
                    elif self.event == 'chat_invite_user' \
                            and not message['action_mid'] == self.SELF_ID:
                        self.event = 'user joined'
                        self.event_user_id = message['action_mid']
                    elif self.event == 'chat_kick_user' \
                        and not message['action_mid'] == self.SELF_ID:
                        self.event = 'user kicked'
                        self.event_user_id = message['action_mid']
                    else:
                        self.event = None

                if self.event:
                    self.raw_text = 'event=' + self.event
                    self.text = self.raw_text
                    self.lower_text = self.raw_text
        

class LongPollSession(Bot):
    def __init__(self):
        self.authorized = False
        self.need_restart = False
        self.bot_thread = None
        self.run_bot = False
        self.running = False
        self.runtime_error = None
        self.reply_count = 0
        self.custom_commands = None

        self.appeals = ('/')
        self.bot_name = u'(Бот)'
        self.mark_type = 'кавычка'
        self.max_captchas = 5
        self.activated = False
        self.use_custom_commands = False
        self.protect_custom_commands = True
        self.openweathermap_api_key = '0'

    def authorization(self, login= '', password= '', token='', logout=False):
        self.authorized, error = \
            vkr.log_in(login=login, password=password, logout=logout)

        return self.authorized, error

    def process_updates(self):
        try:
            if not self.authorized: raise Exception('Not authorized')

            self.black_list = load_blacklist()

            SELF_ID = vkr.get_self_id()[0]
            command = Command(SELF_ID, self.appeals)

            mlpd = None
            last_msg_ids = []
            max_last_msg_ids = 30
            self.captcha_errors = {}
            self.runtime_error = None
            self.running = True

            print('@LAUNCHED')
            while self.run_bot:
                if not mlpd:
                    mlpd, error = vkr.get_message_long_poll_data()
                    if error:
                        raise Exception(error)

                updates, error = \
                    vkr.get_message_updates(ts=mlpd['ts'], pts=mlpd['pts'])
                
                if updates:
                    history = updates[0]
                    mlpd['pts'] = updates[1]
                    messages = updates[2]
                elif 'connection' in error:
                    error = None
                    time.sleep(3)
                    continue
                else:
                    raise Exception(error)

                for message in messages['items']:
                    response_text = ''
                    attachments = []

                    command.load(message)
                    if not command.text or command.msg_id in last_msg_ids:
                        continue

                    if command.was_appeal and command.words[0] == 'blacklist':
                        response_text, self.black_list = \
                            self.blacklist(command, self.black_list)
                    elif command.user_id in self.black_list \
                            or command.chat_id in self.black_list:
                        continue

                    if not response_text \
                            and self.use_custom_commands \
                            and self.custom_commands is not None:
                        response_text, attachments, command = \
                            self.custom_command(command, self.custom_commands)

                    if not (response_text or attachments) and command.was_appeal:

                        if re.match('ping$', command.lower_text):
                            response_text, command = self.pong(command)

                        elif re.match(u'((help)|(помощь)|\?)$',
                                command.words[0].lower()):
                            response_text = self.help(command)

                        elif re.match(u'((скажи)|(say))$', command.words[0].lower()):
                            response_text = self.say(command)

                        elif re.match(u'((посчитай)|(calculate)|=)$', command.words[0].lower()):
                            response_text = self.calculate(command)    

                        elif re.match(u'((простое)|(prime)|%)$', command.words[0].lower()):
                            response_text = self.prime(command)

                        elif re.match(u'((инфа)|(chance)),?$', command.words[0].lower()):
                            response_text = self.chance(command)

                        elif re.match(u'((кто)|(кого)|(who)|(whom))$', command.words[0].lower()):
                            response_text = self.who(command)

                        elif re.match(u'((погода)|(weather))$', command.words[0].lower()):
                            response_text, self.openweathermap_api_key = \
                                self.weather(
                                    command, self.openweathermap_api_key
                                )

                        elif re.match(u'((выучи)|(learn)|\+)$', command.words[0].lower()):
                            self.custom_commands, response_text = self.learn(
                                command,
                                self.custom_commands,
                                protect=self.protect_custom_commands
                                )

                        elif re.match(u'((забудь)|(forgot)|\-)$', command.words[0].lower()):
                            self.custom_commands, response_text = self.forgot(
                                command,
                                self.custom_commands,
                                protect=self.protect_custom_commands
                            )
                            
                        elif re.match('((stop)|\!)$',
                                command.lower_text):
                            response_text = self._stop_bot_from_message(command)

                        elif command.words[0].lower() == 'pause':
                            mlpd = None
                            response_text = self.pause(command)

                        elif command.lower_text == 'activate':
                            response_text, self.activated = \
                                self.activate_bot(command, self.activated)

                        elif command.lower_text == 'deactivate':
                            response_text, self.activated = \
                                self.deactivate_bot(command, self.activated)

                        elif command.words[0].lower() == 'raise':
                            response_text = self._raise_debug_exception(command)

                        elif command.words[0].lower() == 'restart':
                            response_text = self.restart(command)

                        else:
                            response_text = \
                                u'Неизвестная команда. Вы можете использоват' \
                                u'ь {appeal} help для получения списка команд.'

                    if re.match('\s*$', response_text) and not attachments:
                        response_text = ''
                        continue

                    if not self.activated:
                        response_text += \
                            u'\n\nБот не активирован. По вопросам активации ' \
                            u'просьба обратиться к автору: {author}'

                    response_text = self._format_response(response_text, command)

                    if command.mark_msg:
                        if self.mark_type == u'имя':
                            response_text = self.bot_name + ' ' + response_text
                        elif self.mark_type == u'кавычка':
                            response_text += "'"
                        else:
                            raise Exception('Wrong mark type')

                    user_id = None
                    chat_id = None

                    if command.from_chat:
                        chat_id = command.chat_id
                    else:
                        user_id = command.user_id

                    message_to_resend = command.forward_msg
                    msg_id, error = \
                        vkr.send_message(text = response_text,
                                         uid = user_id,
                                         gid = chat_id,
                                         forward = message_to_resend,
                                         attachments = attachments
                                        )
                    if error:
                        if str(error) == 'Captcha needed':
                            captcha = error
                            self.captcha_errors[captcha.sid] = captcha
                            if len(self.captcha_errors) > self.max_captchas:
                                self.captcha_errors.pop(self.captcha_errors.keys()[0])
                            time.sleep(2)
                            continue
                        elif error == 'response code 413':
                            pass # message too long # TODO
                        else:
                            raise Exception(error)

                    self.reply_count += 1

                    if len(last_msg_ids) >= max_last_msg_ids:
                        last_msg_ids = last_msg_ids[1:]
                    last_msg_ids.append(msg_id)

                    time.sleep(1)
                time.sleep(2)
        except:
            import traceback
            self.runtime_error = traceback.format_exc()
            self.run_bot = False

        self.running = False
        self.reply_count = 0
        print('@STOPPED')

    def launch_bot(self):
        self.run_bot = True
        self.bot_thread = Thread(target=self.process_updates)
        self.bot_thread.start()

        while not self.running:
            time.sleep(0.1)
            if self.runtime_error:
                raise Exception(self.runtime_error)
        return True

    def stop_bot(self):
        self.run_bot = False
        self.bot_thread.join()

        return True

    def load_params(self, appeals, activated,
                    bot_name, mark_type,
                    use_custom_commands,
                    protect_custom_commands,
                    openweathermap_api_key):
        if use_custom_commands:
            self.custom_commands = load_custom_commands()

        appeals = appeals.split(':')
        _appeals = []
        for appeal in appeals:
            if appeal and not re.match('\s+$', appeal):
                _appeals.append(appeal.lower())

        if _appeals:
            self.appeals = tuple(_appeals)

        self.activated = activated
        self.bot_name = bot_name
        self.mark_type = mark_type
        self.use_custom_commands = use_custom_commands
        self.protect_custom_commands = protect_custom_commands
        self.openweathermap_api_key = openweathermap_api_key

        return True

    def restart(self, cmd):
        if cmd.out:
            self.need_restart = True
            return u'Начинаю перезагрузку'
        else:
            return u'Отказано в доступе'

    def _stop_bot_from_message(self, cmd):
        if cmd.out:
            self.run_bot = False
            self.runtime_error = 1
            return u'Завершаю работу'
        else:
            return u'Отказано в доступе'

    def _raise_debug_exception(self, cmd):
        if cmd.out:
            words = cmd.words
            del words[0]
            if not words:
                exception_text = 'Default exception text'
            else:
                exception_text = ' '.join(words)
            raise Exception(exception_text)
        else:
            return u'Отказано в доступе'

    def _format_response(self, response_text, command):
        format_dict = {}

        random_ranges = re.findall('{random(\d{1,500})}', response_text)
        for r in random_ranges:
            format_dict['random%s' %r] = random.randrange(int(r) + 1)

        if '{version}' in response_text:
            format_dict['version'] = __version__
        if '{author}' in response_text:
            format_dict['author'] = __author__
        if '{time}' in response_text:
            format_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if '{appeal}' in response_text:
            format_dict['appeal'] = random.choice(self.appeals)
        if '{appeals}' in response_text:
            format_dict['appeals'] = '  '.join(self.appeals)
        if '{bot_name}' in response_text:
            format_dict['bot_name'] = self.bot_name
        if '{my_name}' in response_text:
            name, error = vkr.get_user_name(user_id=command.SELF_ID)
            format_dict['my_name'] = name if name else 'No name'
        if '{my_id}' in response_text:
            format_dict['my_id'] = command.SELF_ID
        if '{user_name}' in response_text:
            name, error = vkr.get_user_name(user_id=command.user_id)
            format_dict['user_name'] = name if name else 'No name'
        if '{user_id}' in response_text:
            format_dict['user_id'] = command.user_id
        if '{random_user_name}' in response_text:
            name, error = vkr.get_user_name(user_id=command.random_chat_user_id)
            format_dict['random_user_name'] = name if name else 'No name'
        if '{random_user_id}' in response_text:
            format_dict['random_user_id'] = command.random_chat_user_id
        if '{chat_name}' in response_text and command.from_chat:
            format_dict['chat_name'] = command.chat_name
        if '{event_user_id}' in response_text and command.event_user_id:
            format_dict['event_user_id'] = command.event_user_id
        if '{event_user_name}' in response_text and command.event_user_id:
            name, error = vkr.get_user_name(user_id=command.event_user_id)
            format_dict['event_user_name'] = name if name else 'No name'

        return safe_format(response_text, **format_dict)
