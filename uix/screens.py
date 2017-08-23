# coding:utf8


import time
import re

from threading import Thread

from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.modalview import ModalView
from kivy.clock import mainthread, Clock
from kivy.core.clipboard import Clipboard
from kivy.config import Config
from kivy.app import App
from kivy import platform

from uix.customcommandblock import CustomCommandBlock, ListDropDown, \
    CommandButton
from uix.editcommandpopup import EditCommandPopup
from uix.widgets import ColoredScreen

from bot.oscclient import OSCClient
from bot.utils import toast_notification, load_custom_commands, \
    save_custom_commands, save_error, CUSTOM_COMMAND_OPTIONS_COUNT, save_token, \
    WHITELIST_FILE_PATH, BLACKLIST_FILE_PATH, BOT_ERROR_FILE_PATH


class AuthScreen(ColoredScreen):
    def __init__(self, **kwargs):
        self.show_password_text = 'Показать пароль'
        self.hide_password_text = 'Скрыть пароль'
        super(AuthScreen, self).__init__(**kwargs)
        self.bot = App.get_running_app().bot
        
    def on_enter(self):
        self.ids.pass_auth.disabled = not self.bot.authorized

    def log_in(self):
        login = self.ids.login_textinput.text
        password = self.ids.pass_textinput.text

        if login and password:
            authorized, error = self.bot.authorization(login=login,
                                                           password=password)
            if authorized:
                self.parent.show_main_screen()
                self.clear_pass_input_text()
            elif error:
                error = str(error)
                if 'password' in error:
                    toast_notification(u'Неправильный логин или пароль')
                else:
                    toast_notification(error)
        return
        
    def clear_pass_input_text(self):
        self.ids.pass_textinput.text = ''

    def update_pass_input_status(self, button):
        if button.text == self.hide_password_text:
            self.ids.pass_textinput.password = True
            button.text = self.show_password_text
        else:
            self.ids.pass_textinput.password = False
            button.text = self.hide_password_text


class TwoFAKeyEnterPopup(ModalView):
    def paste_twofa_code(self, textinput):
        clipboard_data = Clipboard.paste()
        if type(clipboard_data) in (str, unicode) and re.match('\d+$', clipboard_data):
            textinput.text = clipboard_data
        else:
            toast_notification(u'Ошибка при вставке')

    def twofa_auth(self, code):
        if not code:
            return

        def auth_handler(*args):
            return code, True

        self.vk.error_handlers[-2] = auth_handler

        try:
            response = self.vk.twofactor(self.auth_response_page)
        except Exception as e:
            toast_notification(str(e))
        else:
            app = App.get_running_app()
            app.bot.authorized = True

            self.vk.save_cookies()
            self.vk.api_login()
            save_token(token=self.vk.token['access_token'])

            if app.manager.current_screen.name == 'auth_screen':
                app.manager.show_main_screen()

        self.dismiss()

    def open(self, vk, auth_response_page, **kwargs):
        self.vk = vk
        self.auth_response_page = auth_response_page
        super(TwoFAKeyEnterPopup, self).open(**kwargs)


class CaptchaPopup(ModalView):
    def open(self, captcha, **kwargs):
        self.captcha = captcha
        self.ids.image.source = captcha.get_url()
        super(CaptchaPopup, self).open(**kwargs)

    def retry_request(self, key):
        if not key:
            return
        try:
            response = self.captcha.try_again(key) # None
        except Exception as e:
            e = str(e)
            if 'password' in e:
                toast_notification(u'Неправильный логин или пароль')
            else:
                toast_notification(e)
        else:
            app = App.get_running_app()
            app.bot.authorized = True

            self.captcha.vk.api_login()
            save_token(token=self.captcha.vk.token['access_token'])

            if app.manager.current_screen.name == 'auth_screen':
                app.manager.show_main_screen()

        self.dismiss()


class InfoPopup(ModalView):
    pass


class MainScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.bot = App.get_running_app().bot
        self.launch_bot_text = 'Включить бота'
        self.launching_bot_text = 'Запуск (отменить)' 
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text
        self.logging_level = int(
            App.get_running_app().config.getdefault(
                'General', 'logging_level', 1
            )
        )
        self.max_log_lines = int(
            App.get_running_app().config.getdefault(
                'General', 'max_log_lines', 50
            )
        )
        self.log_queue = []
        self.log_check_thread = Thread(target=self.read_log_queue)
        self.log_check_thread.start()
        self.service = OSCClient(self)

    def show_info(self):
        InfoPopup().open()

    def on_main_btn_press(self):
        if self.ids.main_btn.text == self.launch_bot_text:
            self.put_log_to_queue(u'Начинаю запуск бота', 1, time.time())
            self.ids.main_btn.text = self.launching_bot_text
            self.service.start()
        else:
            self.service.stop()
            self.put_log_to_queue(u'Бот полностью остановлен', 2, time.time())
            self.ids.main_btn.text = self.launch_bot_text

    def update_answers_count(self, new_answers_count):
        self.ids.actionprevious.title = 'Ответов: %s' % new_answers_count

    def read_log_queue(self):
        while True:
            if not self.log_queue:
                continue

            _log_queue = sorted(self.log_queue, cmp=lambda x,y: cmp(x[2], y[2]))
            new_lines = ''

            for message in _log_queue:
                self.log_queue.remove(message)

                if message[1] >= self.logging_level:
                    new_lines += time.strftime(
                        '\n[%H:%M:%S] ', time.localtime(message[2])
                    ) + message[0]

            new_lines = new_lines % \
                {
                'whitelist_file': WHITELIST_FILE_PATH,
                'blacklist_file': BLACKLIST_FILE_PATH,
                'bot_error_file': BOT_ERROR_FILE_PATH
                }

            log_text = self.ids.logging_panel.text
            new_log_text = log_text + new_lines
            indent_num = new_log_text.count('\n')

            while indent_num > self.max_log_lines:
                new_log_text = new_log_text[new_log_text.index('\n') + 1:]
                indent_num -= 1

            self.ids.logging_panel.text = new_log_text

            time.sleep(0.33)

    def put_log_to_queue(self, line, log_importance, time):
        self.log_queue.append((line, log_importance, time))

    def logout(self):
        self.bot.authorization(logout=True)
        self.parent.show_auth_screen()


class CustomCommandsScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.edit_popup = EditCommandPopup()
        self.included_keys = []
        self.max_command_preview_text_len = 47

    def on_enter(self):
        self.custom_commands = load_custom_commands()
        if not self.custom_commands and type(self.custom_commands) is not dict:
            toast_notification(u'Повреждён файл пользовательских команд')
            Clock.schedule_once(self.leave, .1)
        else:
            for key in sorted(self.custom_commands.keys()):
                for item in sorted(self.custom_commands[key]):
                    if type(item) is not list or len(item)\
                            < CUSTOM_COMMAND_OPTIONS_COUNT + 1:
                        self.custom_commands[key].remove(item)
                        if type(item) is not list:
                            item = [item]
                        while len(item) < CUSTOM_COMMAND_OPTIONS_COUNT + 1:
                            item.append(0)
                        self.custom_commands[key].append(item)
                        save_custom_commands(self.custom_commands)

                self.custom_commands[key] = sorted(
                    self.custom_commands[key], key=lambda x: x[0])
                if key not in self.included_keys:
                    self.add_command(key, self.custom_commands[key])

    def leave(self, delay=None):
        self.parent.show_main_screen()

    def open_edit_popup(self, command_button, command_block):
        max_title_len = 27
        title = command_button.command.replace('\n', '  ')
        if len(title) > max_title_len:
            title = title[:max_title_len] + '...'

        self.edit_popup.command_block = command_block
        self.edit_popup.switch_command(
            command_button,
            title=u'Настройка команды «{}»'.format(title)
            )

        self.edit_popup.ids.delete_command_btn.unbind(
            on_release=self.edit_popup.ids.delete_command_btn._callback
            )
        self.edit_popup.ids.apply_btn.unbind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )

        new_delete_callback = lambda x: self.remove_command(
            command_button.command, command_button.response,
            command_button, self.edit_popup.command_block
            )
        new_save_callback = lambda x: self.save_edited_command(
            self.edit_popup.ids.command_textinput.text,
            self.edit_popup.ids.response_textinput.text,
            command_button, self.edit_popup.command_block
            )

        self.edit_popup.ids.delete_command_btn._callback = new_delete_callback
        self.edit_popup.ids.apply_btn._callback = new_save_callback

        self.edit_popup.ids.delete_command_btn.bind(
            on_release=self.edit_popup.ids.delete_command_btn._callback
            )
        self.edit_popup.ids.apply_btn.bind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )

        self.edit_popup.open()

    def open_new_command_popup(self):
        self.edit_popup.switch_to_empty_command()
        self.edit_popup.command_block = None

        create_callback = lambda x: self.create_command(
            self.edit_popup.ids.command_textinput.text,
            self.edit_popup.ids.response_textinput.text,
            )
        self.edit_popup.ids.apply_btn._callback = create_callback

        self.edit_popup.ids.apply_btn.bind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )
        self.edit_popup.open()

    def save_edited_command(self, command, response, command_button, block):
        if not (self.edit_popup.ids.command_textinput.text
                and self.edit_popup.ids.response_textinput.text):
            toast_notification(
                u'Поля с командой и ответом не могут быть пустыми')
            return

        options = self.edit_popup.get_options()

        button_command = command_button.command

        if options != command_button.options:
            self.custom_commands[button_command].remove(
                [command_button.response] + command_button.options)
            self.custom_commands[button_command].append(
                [command_button.response] + options)

            command_button.options = []
            for i in options:
                command_button.options.append(i)
            # command_button.options = options will cause
            # command_button.options is options

            updated_command = []

            if options[0] == 2: # use_regex
                for r in self.custom_commands[button_command]:
                    r[1] = 2
                    updated_command.append(r)

                for button in block.dropdown.container.children:
                    button.options[0] = 2

            else:
                for r in self.custom_commands[button_command]:
                    r[1] = 0
                    updated_command.append(r)

                for button in block.dropdown.container.children:
                    button.options[0] = 0
            
            self.custom_commands[button_command] = updated_command

        if button_command != command:
            if command in self.included_keys:
                toast_notification(u'Такая команда уже существует')
                return
            self.included_keys.remove(button_command)
            self.included_keys.append(command)
            command_button.command = command
            block.command = command
            if len(block.responses) > 1:
                for button in block.dropdown.container.children:
                    button.command = command

            command_preview = command
            command_preview = command_preview.replace('\n', '  ')
            if len(command_preview) > self.max_command_preview_text_len:
                command_preview = \
                    command_preview[:self.max_command_preview_text_len] + '...'
            block.ids.dropdown_btn.text = command_preview

            self.custom_commands[command] = []
            for r in self.custom_commands[button_command]:
                self.custom_commands[command].append(r)
            self.custom_commands.pop(button_command)

        if response != command_button.response:
            self.custom_commands[command].remove(
                [command_button.response] + command_button.options)
            block.responses.remove(command_button.response)

            command_button.response = response

            response_preview = response
            response_preview = response_preview.replace('\n', '  ')
            if len(response_preview) > self.max_command_preview_text_len:
                response_preview = \
                    response_preview[:self.max_command_preview_text_len] + '...'
            command_button.text = response_preview

            block.responses.append(response)

            command_preview = command
            command_preview = command_preview.replace('\n', '  ')
            if len(command_preview) > self.max_command_preview_text_len:
                command_preview = \
                    command_preview[:self.max_command_preview_text_len] + '...'
            block.ids.dropdown_btn.text = command_preview

            self.custom_commands[command].append([response] + options)

        save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()

    def remove_command(self, command, response, command_button, block):
        options = self.edit_popup.get_options()

        if len(block.responses) == 1:
            self.custom_commands.pop(command, None)
            self.included_keys.remove(command)
            self.ids.cc_list.remove_widget(block)
        elif len(block.responses) == 2:
            block.ids.dropdown_btn.unbind(
                on_release=block.ids.dropdown_btn.callback)
            block.dropdown.remove_widget(command_button)

            command_button = block.ids.dropdown_btn
            command_button.command = command
            command_button.response =\
                block.dropdown.container.children[0].response # last child
            block.dropdown.remove_widget(block.dropdown.container.children[0])

            command_button.options = self.custom_commands[command][0][1:]

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)
            block.responses.remove(response)
            self.custom_commands[command].remove(
                [response] + options)
            block.dropdown.dismiss()
        else:
            self.custom_commands[command].remove(
                [response] + options)
            block.dropdown.remove_widget(command_button)
            block.responses.remove(response)
            block.dropdown.dismiss()

        save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()

    def create_command(self, command, response):
        if not (self.edit_popup.ids.command_textinput.text
                and self.edit_popup.ids.response_textinput.text):
            toast_notification(
                u'Поля с командой и ответом не могут быть пустыми')
            return

        options = self.edit_popup.get_options()

        if command not in self.included_keys:
            self.custom_commands[command] = [[response] + options]
            self.add_command(command, [[response] + options])
        else:
            for child in self.ids.cc_list.children:
                if child.command == command:
                    block = child
                    break

            if len(self.custom_commands[command]) == 1:
                old_command_button = CommandButton(
                    text=block.ids.dropdown_btn.response)
                old_command_button.command = block.ids.dropdown_btn.command
                old_command_button.response = block.ids.dropdown_btn.response
                del block.ids.dropdown_btn.command
                del block.ids.dropdown_btn.response

                old_command_button.options = block.ids.dropdown_btn.options

                callback = lambda x: self.open_edit_popup(x, block)
                old_command_button.callback = callback
                old_command_button.bind(on_release=old_command_button.callback)

                block.ids.dropdown_btn.unbind(
                    on_release=block.ids.dropdown_btn.callback)
                dropdown_callback = block.dropdown.open
                block.ids.dropdown_btn.callback = dropdown_callback
                block.ids.dropdown_btn.bind(
                    on_release=block.ids.dropdown_btn.callback)

                block.dropdown.add_widget(old_command_button)

            response_preview = response
            response_preview = response_preview.replace('\n', '  ')
            if len(response_preview) > self.max_command_preview_text_len:
                response_preview = \
                    response_preview[:self.max_command_preview_text_len] + '...'
            command_button = CommandButton(text=response_preview)
            command_button.command = command
            command_button.response = response
            command_button.options = options

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            block.dropdown.add_widget(command_button)
            block.responses.append(response)
            self.custom_commands[command].append([response] + options)

            updated_command = []

            if options[0] == 2: # use_regex
                for r in self.custom_commands[command]:
                    r[1] = 2
                    updated_command.append(r)

                for button in block.dropdown.container.children:
                    button.options[0] = 2
            else:
                for r in self.custom_commands[command]:
                    r[1] = 0
                    updated_command.append(r)

                for button in block.dropdown.container.children:
                    button.options[0] = 0

            self.custom_commands[command] = updated_command

        save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()

    def add_command(self, command, response):
        dropdown = ListDropDown()
        block = CustomCommandBlock(dropdown=dropdown)
        
        for item in response:
            if len(response) > 1:
                response_preview = item[0]
                response_preview = response_preview.replace('\n', '  ')
                if len(response_preview) > self.max_command_preview_text_len:
                    response_preview = \
                        response_preview[:self.max_command_preview_text_len] + '...'
                command_button = CommandButton(text=response_preview)
            else:
                command_button = block.ids.dropdown_btn

            command_button.command = command
            command_button.response = item[0]
            command_button.options = item[1:]

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            if len(response) > 1:
                block.dropdown.add_widget(command_button)
            block.responses.append(item[0])
        block.command = command

        command_preview = command
        command_preview = command_preview.replace('\n', '  ')
        if len(command_preview) > self.max_command_preview_text_len:
            command_preview = \
                command_preview[:self.max_command_preview_text_len] + '...'
        block.ids.dropdown_btn.text = command_preview

        if len(response) > 1:
            dropdown_callback = block.dropdown.open
            block.ids.dropdown_btn.callback = dropdown_callback
            block.ids.dropdown_btn.bind(
                on_release=block.ids.dropdown_btn.callback)
        self.ids.cc_list.add_widget(block)
        self.included_keys.append(command)

    def sort_blocks(self):
        for widget in sorted(self.ids.cc_list.children):
            self.included_keys.remove(widget.command)
            self.ids.cc_list.remove_widget(widget)

        self.on_enter()


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(Manager, self).__init__(**kwargs)
        self.transition = FadeTransition()
        self.last_screen = None

    def show_auth_screen(self):
        if not 'auth_screen' in self.screen_names:
            self.add_widget(AuthScreen())
        self.current = 'auth_screen'

    def show_main_screen(self):
        if not 'main_screen' in self.screen_names:
            self.add_widget(MainScreen())
        self.current = 'main_screen'

    def show_custom_commands_screen(self):
        if not 'cc_screen' in self.screen_names:
            self.add_widget(CustomCommandsScreen())
        self.current = 'cc_screen'
