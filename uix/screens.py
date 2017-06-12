# coding:utf8


import time
from functools import partial

from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.modalview import ModalView
from kivy.clock import mainthread, Clock
from kivy.app import App
from kivy import platform

from uix.customcommandblock import CustomCommandBlock, ListDropDown, CommandButton
from uix.editcommandpopup import EditCommandPopup

from bot.utils import toast_notification, load_custom_commands, \
    save_custom_commands, save_error, CUSTOM_COMMAND_OPTONS_COUNT


class AuthScreen(Screen):
    def __init__(self, **kwargs):
        self.show_password_text = 'Показать пароль'
        self.hide_password_text = 'Скрыть пароль'
        super(AuthScreen, self).__init__(**kwargs)
        self.session = App.get_running_app().session
        self.twofa_popup = None
        
    def on_enter(self):
        self.ids.pass_auth.disabled = not self.session.authorized

    def log_in(self, twofa_key=''):
        login = self.ids.login_textinput.text
        password = self.ids.pass_textinput.text

        if login and password:
            authorized, error = self.session.authorization(
                                login=login, password=password, key=twofa_key
                                )
            if authorized:
                self.ids.pass_textinput.text = ''
                self.parent.show_main_screen()
                if twofa_key:
                    return True
            elif error:
                if 'code is needed' in error:
                    if not self.twofa_popup:
                        self.twofa_popup = TwoFAKeyEnterPopup(self)
                    self.twofa_popup.open()
                    return
                elif 'incorrect password' in error:
                    toast_notification(u'Неправильный логин или пароль')
                else:
                    toast_notification(error)
                    return
        self.ids.pass_textinput.text = ''

    def update_pass_input_status(self, button):
        if button.text == self.hide_password_text:
            self.ids.pass_textinput.password = True
            button.text = self.show_password_text
        else:
            self.ids.pass_textinput.password = False
            button.text = self.hide_password_text


class TwoFAKeyEnterPopup(ModalView):
    def __init__(self, auth_screen, **kwargs):
        super(TwoFAKeyEnterPopup, self).__init__(**kwargs)
        self.auth_screen = auth_screen

    def twofa_auth(self, code):
        if code:
            if self.auth_screen.log_in(twofa_key=code):
                self.dismiss()
            self.ids.textinput.text = ''


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.bot_check_event = Clock.schedule_interval(self.check_if_bot_active, 1)
        self.bot_check_event.cancel()
        self.session = App.get_running_app().session
        self.launch_bot_text = 'Включить бота'
        self.launching_bot_text = 'Запуск (отменить)' 
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text
        if platform == 'android':
            from bot.oscclient import OSCClient
            self.service = OSCClient(self)

    def show_manual(self):
        pass

    def on_enter(self):
        pass

    @mainthread
    def on_main_btn_press(self):
        config = App.get_running_app().config

        if self.ids.main_btn.text == self.launch_bot_text:
            self.launch_bot(config)
        else:
            self.stop_bot(config)

    def launch_bot(self, config):
        if platform == 'android':
            self.ids.main_btn.text = self.launching_bot_text
            self.service.start()
        else:
            appials = config.get('General', 'appeals')
            self.activation_status = config.get('General', 'bot_activated')
            use_custom_commands = config.get('General', 'use_custom_commands')
            protect_custom_commands = config.get('General', 'protect_cc')

            self.session.load_params(
            	       appials,
                    activated=self.activation_status == 'True',
                    use_custom_commands=use_custom_commands == 'True',
                    protect_custom_commands=protect_custom_commands == 'True'
                    )
            self.session.launch_bot()
            self.bot_check_event()

            self.ids.main_btn.text = self.stop_bot_text

    def stop_bot(self, config):
        if platform == 'android':
            self.service.stop()
        else:
            self.bot_check_event.cancel()
            bot_stopped = False

            while not bot_stopped:
                bot_stopped, new_activation_status = self.session.stop_bot()

            if new_activation_status != self.activation_status:
                config.set('General', 'bot_activated', str(new_activation_status))
                config.write()

        self.ids.main_btn.text = self.launch_bot_text

    def update_answers_count(self, new_answers_count):
        self.ids.answers_count_lb.text = 'Ответов: {}'.format(new_answers_count)

    def logout(self):
        self.session.authorization(logout=True)
        self.parent.show_auth_screen()
    
    def show_bot_error(self, error_text):
        error_text = error_text.decode('unicode-escape')
        toast_notification(error_text)
        save_error(error_text, from_bot=True)

    def check_if_bot_active(self, tick):
        self.update_answers_count(self.session.reply_count)
        if self.ids.main_btn.text == self.stop_bot_text and\
                not self.session.running:
            self.bot_check_event.cancel()
            self.ids.main_btn.text = self.launch_bot_text

            if self.session.runtime_error:
                error = self.session.runtime_error
                try:
                    error = error[error.index('Exception: '):]
                    toast_notification(error)
                except:
                    raise Exception(error)


class CustomCommandsScreen(Screen):
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.included_keys = []

    def on_enter(self):
        self.custom_commands = load_custom_commands()
        if not self.custom_commands and type(self.custom_commands) is not dict:
            toast_notification(u'Повреждён файл пользовательских команд')
            Clock.schedule_once(self.leave, .1)
        else:
            for key in sorted(self.custom_commands.keys()):
                for item in sorted(self.custom_commands[key]):
                    # FIXME do not work without sorted()
                    if type(item) is not list or len(item)\
                            < CUSTOM_COMMAND_OPTONS_COUNT + 1:
                        self.custom_commands[key].remove(item)
                        if type(item) is not list:
                            item = [item]
                        while len(item) < CUSTOM_COMMAND_OPTONS_COUNT + 1:
                            item.append(0)
                        self.custom_commands[key].append(item)
                        save_custom_commands(self.custom_commands)

                self.custom_commands[key] = sorted(self.custom_commands[key], key=lambda x: x[0])
                if key not in self.included_keys:
                    self.add_command(key, self.custom_commands[key])

    def leave(self, delay=None):
        self.parent.show_main_screen()

    def open_edit_popup(
                self, command, response, use_regex, force_unmark,
                force_forward, appeal_only, disable,
                command_button, command_block, *args
                ):
        MAX_TITLE_LEN = 30
        title = command.replace('\n', ' ')
        if len(command) > MAX_TITLE_LEN:
            title = command[:MAX_TITLE_LEN] + '...'
        popup = EditCommandPopup(
            title=u'Настройка команды «{}»'.format(title),
            command_text=command,
            response_text=response,
            use_regex=use_regex,
            force_unmark=force_unmark,
            force_forward=force_forward,
            appeal_only=appeal_only,
            disable=disable,
            command_button=command_button,
            command_block=command_block
            )
        popup.ids.delete_command_btn.bind(
            on_release=lambda x: self.remove_command(
                command_button.command,
                command_button.response,
                command_button,
                popup.command_block,
                popup
                )
            )
        popup.ids.apply_btn.bind(
            on_release=lambda x: self.save_edited_command(
                popup.ids.command_textinput.text,
                popup.ids.response_textinput.text,
                popup.command_button,
                popup.command_block,
                popup
                )
            )
        popup.open()

    def open_new_command_popup(self):
        popup = EditCommandPopup(
            title='Настройка новой команды',
            command_text='',
            response_text='',
            command_button=None,
            command_block=None
            )
        popup.ids.apply_btn.bind(
            on_release=lambda x: self.create_command(
                popup.ids.command_textinput.text,
                popup.ids.response_textinput.text,
                popup
                )
            )
        popup.open()

    def save_edited_command(
                self, command, response,
                command_button, block, popup
                ):
        try:
            command = command.decode('utf8')
        except UnicodeEncodeError:
            pass
        try:
            response = response.decode('utf8')
        except UnicodeEncodeError:
            pass

        if not (popup.ids.command_textinput.text and popup.ids.response_text.text):
            toast_notification(u'Поля с командой и ответом не могут быть пустыми')
            return

        button_command = command_button.command
        if button_command != command:
            if command in self.included_keys:
                toast_notification(u'Такая команда уже есть')
                return
            self.custom_commands.pop(button_command)
            self.included_keys.remove(button_command)
            self.included_keys.append(command)
            command_button.command = command
            block.command = command
            if len(block.responses) > 1:
                block.ids.dropdown_btn.text = command
                for button in block.dropdown.container.children:
                    button.command = command
                    button.unbind(on_release=button.callback)
                    callback = partial(
                        self.open_edit_popup,
                        button.command,
                        button.response,
                        button,
                        block
                        )
                    button.callback = callback
                    button.bind(on_release=button.callback)
                command_button.text = response
            else:
                command_button.unbind(on_release=command_button.callback)
                callback = partial(
                    self.open_edit_popup,
                    command_button.command,
                    command_button.response,
                    command_button,
                    block
                    )
                command_button.callback = callback
                command_button.bind(on_release=command_button.callback)
                command_button.text = command

        if response != command_button.response:
            block.responses.remove(command_button.response)
            command_button.response = response
            command_button.text = response
            block.responses.append(response)
            command_button.unbind(on_release=command_button.callback)
            callback = partial(
                self.open_edit_popup,
                command_button.command,
                command_button.response,
                command_button,
                block
                )
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)
        self.custom_commands[command] = []
        for response in block.responses:
            self.custom_commands[command].append(response)
        # self.custom_commands[command] = responses
        # will cause
        # self.custom_commands[command] is responses

        save_custom_commands(self.custom_commands)
        popup.dismiss()

    def remove_command(self, command, response, command_button, block, popup):
        if len(block.responses) == 1:
            self.custom_commands.pop(command, None)
            self.included_keys.remove(command)
            self.ids.cc_list.remove_widget(block)
        elif len(block.responses) == 2:
            block.ids.dropdown_btn.unbind(on_release=block.ids.dropdown_btn.callback)
            block.dropdown.remove_widget(command_button)

            command_button = block.ids.dropdown_btn
            command_button.command = command
            command_button.response = block.dropdown.container.children[0].response # last child
            block.dropdown.remove_widget(block.dropdown.container.children[0])

            callback = partial(
                self.open_edit_popup,
                command_button.command,
                command_button.response,
                command_button,
                block
                )
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)
            block.responses.remove(response)
            self.custom_commands[command].remove(response)
            block.dropdown.dismiss()
        else:
            self.custom_commands[command].remove(response)
            block.dropdown.remove_widget(command_button)
            block.responses.remove(response)
            block.dropdown.dismiss()

        save_custom_commands(self.custom_commands)
        popup.dismiss()

    def create_command(self, command, response, popup):
        try:
            command = command.decode('utf8')
        except UnicodeEncodeError:
            pass
        try:
            response = response.decode('utf8')
        except UnicodeEncodeError:
            pass

        if not (popup.ids.command_textinput.text and popup.ids.response_text.text):
            toast_notification(u'Поля с командой и ответом не могут быть пустыми')
            return

        if command not in self.included_keys:
            self.custom_commands[command] = [response]
            self.add_command(command, [response])
        else:
            for child in self.ids.cc_list.children:
                if command == child.command:
                    block = child
                    break

            if len(self.custom_commands[command]) == 1:
                old_command_button = CommandButton(text=block.ids.dropdown_btn.response)
                old_command_button.command = block.ids.dropdown_btn.command
                old_command_button.response = block.ids.dropdown_btn.response
                del block.ids.dropdown_btn.command
                del block.ids.dropdown_btn.response

                callback = partial(
                    self.open_edit_popup,
                    old_command_button.command,
                    old_command_button.response,
                    old_command_button,
                    block
                    )
                old_command_button.callback = callback
                old_command_button.bind(on_release=old_command_button.callback)

                block.ids.dropdown_btn.unbind(on_release=block.ids.dropdown_btn.callback)
                dropdown_callback = block.dropdown.open
                block.ids.dropdown_btn.callback = dropdown_callback
                block.ids.dropdown_btn.bind(on_release=block.ids.dropdown_btn.callback)

                block.dropdown.add_widget(old_command_button)

            command_button = CommandButton(text=response)
            command_button.command = command
            command_button.response = response
            callback = partial(
                self.open_edit_popup,
                command_button.command,
                command_button.response,
                command_button,
                block
                )
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            block.dropdown.add_widget(command_button)
            block.responses.append(response)
            self.custom_commands[command].append(response)

        save_custom_commands(self.custom_commands)
        popup.dismiss()

    def add_command(self, command, response):
        dropdown = ListDropDown()
        block = CustomCommandBlock(dropdown=dropdown)
        
        for item in response:
            if len(response) > 1:
                command_button = CommandButton(text=item[0])
            else:
                command_button = block.ids.dropdown_btn

            command_button.command = command
            command_button.response = item[0]
            command_button.use_regex = item[1]
            command_button.force_unmark = item[2]
            command_button.force_forward = item[3]
            command_button.appeal_only = item[4]
            command_button.disable = item[5]
            callback = partial(
                self.open_edit_popup,
                command_button.command,
                command_button.response,
                command_button.use_regex,
                command_button.force_unmark,
                command_button.force_forward,
                command_button.appeal_only,
                command_button.disable,
                command_button,
                block
                )
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            if len(response) > 1:
                block.dropdown.add_widget(command_button)
            block.responses.append(item)
        block.command = command

        block.ids.dropdown_btn.text = command
        if len(response) > 1:
            dropdown_callback = block.dropdown.open
            block.ids.dropdown_btn.callback = dropdown_callback
            block.ids.dropdown_btn.bind(on_release=block.ids.dropdown_btn.callback)
        self.ids.cc_list.add_widget(block)
        self.included_keys.append(command)

    def sort_blocks(self):
        for widget in sorted(self.ids.cc_list.children):
            # FIXME do not work without sorted()
            self.included_keys.remove(widget.command)
            self.ids.cc_list.remove_widget(widget)

        self.on_enter()


class Root(ScreenManager):
    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)
        self.transition = FadeTransition()

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
