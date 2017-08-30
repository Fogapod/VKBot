# coding:utf8


import time
import re
import random

from threading import Thread

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.modalview import ModalView
from kivy.clock import mainthread, Clock
from kivy.core.clipboard import Clipboard
from kivy.properties import NumericProperty
from kivy.animation import Animation

from uix.customcommandblock import CustomCommandBlock, ListDropDown, \
    CommandButton
from uix.editcommandpopup import EditCommandPopup
from uix.widgets import ColoredScreen

from bot.utils import toast_notification, load_custom_commands, \
    save_custom_commands, save_error, CUSTOM_COMMAND_OPTIONS_COUNT, save_token, \
    WHITELIST_FILE_PATH, BLACKLIST_FILE_PATH, BOT_ERROR_FILE_PATH, \
    CUSTOM_COMMANDS_FILE_PATH


class AuthPopup(ModalView):
    def __init__(self, app, **kwargs):
        self.show_password_text = 'Показать пароль'
        self.hide_password_text = 'Скрыть пароль'
        self.app = app
        super(AuthPopup, self).__init__(**kwargs)


    def log_in(self):
        login = self.ids.login_textinput.text
        password = self.ids.pass_textinput.text

        if login and password:
            self.app.osc_service.send_auth_request(login, password)
            self.dismiss()


    def update_pass_input_status(self, button):
        self.ids.pass_textinput.password = not self.ids.pass_textinput.password

        if self.ids.pass_textinput.password:
            button.text = self.show_password_text
        else:
            button.text = self.hide_password_text


    def on_dismiss(self):
        if self.ids.login_textinput.text != '':
            self.app._cached_login = self.ids.login_textinput.text
        else:
            self.app._cached_login = None

        if self.ids.pass_textinput.text != '':
            self.app._cached_password = self.ids.pass_textinput.text
        else:
            self.app._cached_login = None


class TwoFAPopup(ModalView):
    def __init__(self, app, **kwargs):
        self.app = app
        super(TwoFAPopup, self).__init__(**kwargs)

    def paste_twofa_code(self, textinput):
        clipboard_data = Clipboard.paste()
        if type(clipboard_data) in (str, unicode) and re.match('\d+$', clipboard_data):
            textinput.text = clipboard_data
        else:
            toast_notification(u'Ошибка при вставке')

    def send_code(self, code):
        if not code:
            return

        self.app.osc_service.send_twofactor_code(code)
        self.dismiss()


class CaptchaPopup(ModalView):
    def __init__(self, app, captcha_img_url, **kwargs):
        self.app = app
        self.captcha_url = captcha_img_url
        super(CaptchaPopup, self).__init__(**kwargs)

    def send_code(self, code):
        if not code:
            return

        self.app.osc_service.send_captcha_code(code)
        self.dismiss()


class InfoPopup(ModalView):
    pass


class LoadingPopup(ModalView):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super(LoadingPopup, self).__init__(**kwargs)
        angle = 360
        if random.choice((0, 1)):
            angle = -angle

        anim = Animation(angle=angle, duration=2)
        anim += Animation(angle=angle, duration=2)
        anim.repeat = True
        anim.start(self)

    def on_angle(self, item, angle):
        if angle in (360, -360):
            item.angle = 0


class MainScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.launch_bot_text = 'Включить бота'
        self.launching_bot_text = 'Запуск (отменить)' 
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text
        self.logging_level = int(
            self.app.config.getdefault(
                'General', 'logging_level', 1
            )
        )
        self.max_log_lines = int(
            self.app.config.getdefault(
                'General', 'max_log_lines', 50
            )
        )
        self.log_queue = []
        self.continue_reading_log_queue = True
        self.log_check_thread = Thread(target=self.read_log_queue)
        self.log_check_thread.start()


    def show_info(self):
        InfoPopup().open()


    def on_main_btn_press(self):
        if self.ids.main_btn.text == self.launch_bot_text:
            self.ids.main_btn.text = self.launching_bot_text
            self.app.osc_service.start()
        else:
            self.app.osc_service.stop()
            self.ids.main_btn.text = self.launch_bot_text


    def update_answers_count(self, new_answers_count):
        self.ids.actionprevious.title = 'Ответов: %s' % new_answers_count


    def read_log_queue(self):
        while self.continue_reading_log_queue:
            time.sleep(0.33)
            if not self.log_queue \
                    or not str(
                        self.app.manager.current_screen
                    )[14:-2] == 'main_screen':

                continue

            try:
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
                    'bot_error_file': BOT_ERROR_FILE_PATH,
                    'custom_commands_file': CUSTOM_COMMANDS_FILE_PATH
                    }

                log_text = self.ids.logging_panel.text
                new_log_text = log_text + new_lines
                indent_num = new_log_text.count('\n')

                while indent_num > self.max_log_lines:
                    new_log_text = new_log_text[new_log_text.index('\n') + 1:]
                    indent_num -= 1

                self.ids.logging_panel.text = new_log_text

            except:
                self.ids.logging_panel.text += u'\n[b]Возникла ошибка! Не могу отобразить лог[/b]'


    def stop_log_check_thread(self):
        self.continue_reading_log_queue = False
        if self.log_check_thread:
            self.log_check_thread.join()


    def put_log_to_queue(self, line, log_importance, time):
        self.log_queue.append((line, log_importance, time))


    def logout(self):
        self.put_log_to_queue(u'Записываю пустой токен...', 0, time.time())
        save_token('')
        self.put_log_to_queue(u'[b]Сессия сброшена[/b]', 2, time.time())


class CustomCommandsScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.edit_popup = EditCommandPopup()
        self.included_keys = []
        self.max_command_preview_text_len = 47


    def on_enter(self):
        # App.get_running_app().open_loading_popup()
        Clock.schedule_once(self.sort_blocks)

    def sort_blocks(self, *args):
        for widget in sorted(self.ids.cc_list.children):
            self.included_keys.remove(widget.command)
            self.ids.cc_list.remove_widget(widget)

        self.custom_commands = load_custom_commands()

        if not self.custom_commands and type(self.custom_commands) is not dict:
            toast_notification(u'Повреждён файл пользовательских команд')
            Clock.schedule_once(self.leave, .1)

        else:
            for key in sorted(self.custom_commands.keys()):
                for item in sorted(self.custom_commands[key]):
                    if type(item) is not list or len(item) \
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

        # App.get_running_app().close_loading_popup()


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

            command_button.options = options[:]
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


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(Manager, self).__init__(**kwargs)
        self.transition = FadeTransition()
        self.last_screen = None

    def show_main_screen(self):
        if not 'main_screen' in self.screen_names:
            self.add_widget(MainScreen())
        self.current = 'main_screen'

    def show_custom_commands_screen(self):
        if not 'cc_screen' in self.screen_names:
            self.add_widget(CustomCommandsScreen())
        self.current = 'cc_screen'
