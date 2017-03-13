# -*- coding: utf-8 -*-
import time
import re
import math
from threading import Thread

from utils import parse_input, load_custom_commands
import vkrequests as vkr

from utils import PATH
from utils import DATA_PATH

__version__ = '0.0.3'
AUTHOR_VK_ID = 180850898
__author__ = 'Eugene Ershov - https://vk.com/id%d' % AUTHOR_VK_ID

__help__ = '''
Версия: {v}

Я умею:
*Говорить то, что вы попросите
(/say ... |/скажи ... )
*Производить математические операции
(/calculate ... |/посчитай ... ) =
*Проверять, простое ли число
(/prime ... |/простое ... ) %
*Вызывать помощь
(/help |/помощь ) ?


Автор: {author}

В конце моих сообщений ставится знак верхней кавычки
'''.format(\
    v = __version__, author = __author__
)


class Bot(object):
    def help(self):
        return __help__

    def say(self, words):
        argument_required = self._argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        text = ' '.join(words)
        return text

    def calculate(self, words):
        argument_required = self._argument_missing(words)
        if argument_required:
            return argument_required

        if words[0].startswith('='):
            words[0] = words[0][1:]
        else:
            del words[0]
        words = ''.join(words).lower()
        if not re.match(u'[^\d+\-*/:().,^√πe]', words) or re.match('(sqrt\(\d+\))|(pi)', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π', 'math.pi', words)
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
                result = str(eval(words))
            except SyntaxError:
                result = 'Ошибка [0]'
            except NameError:
                result = 'Ошибка [1]'
            except AttributeError:
                result = 'Ошибка [2]'        
            except ZeroDivisionError:
                result = 'Деление на 0'
            except OverflowError:
                result = 'Слишком большой результат'
        else:
            result = 'Не математическая операция'
        return result

    def prime(self, words):
        argument_required = self._argument_missing(words)
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
                    luc_number, last_luc_number = last_luc_number + luc_number, luc_number
                            
            if input_number != 0:
                is_prime = True if (luc_number - 1) % input_number == 0 else False
                result = 'Является простым числом' if is_prime else 'Не является простым числом'
            else:
                result = '0 не является простым числом'
        else:
            result = 'Дано неверное или слишком большое значение'
        return result

    def activate_bot(self, message):
        if message['user_id'] == AUTHOR_VK_ID and message['title'] != u' ... ':
            return 'Активация прошла успешно', True
        else:
            return 'Отказано в доступе', False

    def deactivate_bot(self, message):
        if message['user_id'] == AUTHOR_VK_ID and message['title'] != u' ... ':
            return 'Деактивация прошла успешно', False
        else:
            return 'Отказано в доступе', True

    def _argument_missing(self, words):
        if len(words) == 1:
            return 'Команду необходимо использовать с аргументом'
        else:
            return False


class LongPollSession(Bot):
    def __init__(self):
        self.activated = False
        self.authorized = False
        self.update_processing = None
        self.run_bot = False
        self.running = False
        self.runtime_error = None
        self.reply_count = 0

    def authorization(self, login= '', password= '', key='', logout=False):
        token_path = DATA_PATH + 'token.txt'
        authorized = False
        token = None
        error = None
        if logout:
            open(token_path, 'w').close()
            self.authorized = False
            return authorized, error

        if not (login and password):
            try:
                with open(token_path, 'r') as token_file:
                    lines = token_file.readlines()
                    if lines:
                        token = lines[0][:-1]
            except:
                token = None
                open(token_path, 'w').close()

            if token:
                response, error = vkr.log_in(token=token)
                if response and not error:
                    authorized = True
                    if error:
                        if 'connection' in error:
                            pass
                        elif 'invalid access_token' in error:
                            open(token_path, 'w').close()
        else:
            new_token, error = vkr.log_in(login=login, password=password, key=key)
            if new_token and not error:
                with open(token_path, 'w') as token_file:
                    token_file.write('{}\n{}'.format(\
                        new_token, 'НИКОМУ НЕ ПОКАЗЫВАЙТЕ СОДЕРЖИМОЕ ЭТОГО ФАЙЛА'
                        )
                    )
                authorized = True
            elif self.authorized:
                return authorized, error

        self.authorized = authorized
        return authorized, error

    def _process_updates(self):
        if not self.authorized: return
        if self.use_custom_commands:
            self.custom_commands = load_custom_commands()
        else:
            self.custom_commands = None

        mlpd = vkr.get_message_long_poll_data()[0]
        last_response_text = ''
        self.runtime_error = None
        self.running = True

        print('__LAUNCHED__')
        while self.run_bot:
            try:
                time.sleep(1)
                response = vkr.get_message_updates(ts=mlpd['ts'],pts=mlpd['pts'])[0]
                print(response)
                if response[0]:
                    updates = response[0]
                    mlpd['pts'] = response[1]
                    messages = response[2]
                else:
                    time.sleep(1)
                    continue
                response = None

                for message in messages['items']:
                    message_text = message['body']
                    if message_text and message_text != last_response_text:
                        mark_msg = True
                    else:
                        continue

                    message_text = parse_input(message_text)
                    words = message_text.split(' ')

                    if re.sub('^( )*', '', words[0]).startswith('/'):
                        words[0] = words[0][1:]
                        if words[0].startswith('/'):
                            mark_msg = False
                            words[0] = words[0][1:]   

                        if re.match(u'(^help)|(^помощь)|(^info)|(^инфо)|(^информация)|^\?$',\
                            words[0].lower()):
                            response_text = self.help()

                        elif re.match(u'(^скажи)|(^say)$', words[0].lower()):
                            response_text = self.say(words)

                        elif re.match(u'(^посчитай)|(^calculate)$', words[0].lower()) or\
                             words[0].startswith('='):
                            response_text = self.calculate(words)    

                        elif re.match(u'(^простое)|(^prime)|%$', words[0].lower()):
                            response_text = self.prime(words)

                        elif re.match(u'(^stop)|(^выйти)|(^exit)|(^стоп)|(^terminate)|(^завершить)|(^close)|^!$',\
                    	     words[0].lower()):
                            response_text = self._stop_bot_from_message(message)

                        elif words[0].lower() == 'activate':
                            response_text, self.activated = self.activate_bot(message)

                        elif words[0].lower() == 'deactivate':
                            response_text, self.activated = self.deactivate_bot(message)

                        else:
                            response_text = 'Неизвестная команда. Вы можете использовать /help для получения списка команд.'
                    else:
                        if self.custom_commands and\
                          message_text.lower() in self.custom_commands.keys():
                            response_text = self.custom_commands[message_text.lower()]
                            mark_msg = False
                        else:
                            continue

                    if not self.activated:
                        try:
                            response_text += '\n\nБот не активирован. По вопросам активации просьба обратиться к автору: %s' % __author__
                        except UnicodeDecodeError: # TODO
                            response_text += u'\n\nБот не активирован. По вопросам активации просьба обратиться к автору: %s' % __author__

                    if message['title'] != u' ... ': # messege from chat
                        message_to_resend = message['id']
                        chat_id = message['chat_id']
                        user_id = None
                    else:
                        message_to_resend = None
                        chat_id = None
                        user_id = message['user_id']

                    response_text += "'" if mark_msg else ''
                    vkr.send_message(
                        text = response_text,
                        uid = user_id,
                        gid = chat_id,
                        forward = message_to_resend
                    )
                    last_response_text = response_text
                    self.reply_count += 1

            except Exception as e:
                self.runtime_error = str(e)
                self.run_bot = False

        self.running = False
        self.reply_count = 0
        print('__STOPPED__')

    def start_bot(self, activated=False, use_custom_commands=False):
        self.activated = activated
        self.use_custom_commands = use_custom_commands
        self.run_bot = True

        self.update_processing = Thread(target=self._process_updates)
        self.update_processing.start()

        while not self.running: continue
        return True

    def stop_bot(self):
        self.run_bot = False

        while self.running: continue
        self.update_processing = None
        return True, self.activated

    def _stop_bot_from_message(self, message):
        if message['out']:
            self.run_bot = False
            return 'Завершаю работу'
        else:
            return 'Отказано в доступе'


if __name__ == '__main__':
    session = LongPollSession()
    DATA_PATH = PATH + DATA_PATH
    while not session.authorized:
        response, error = session.authorization()
        if not response:
            LOGIN = raw_input('login:')
            PASSWORD = raw_input('password:')
            response, error = session.authorization(login=LOGIN, password=PASSWORD)

        if error and 'code is needed' in error:
            key = raw_input('key:')
            response, error = session.authorization(login=LOGIN, password=PASSWORD, key=key)

    print('\tУспешная авторизация\n')
    session.start_bot()