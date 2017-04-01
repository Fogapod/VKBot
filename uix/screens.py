#-*- coding:utf-8 -*-


from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.clock import mainthread, Clock
from kivy.app import App

from uix.customcommandblock import CustomCommandBlock
from uix.editcommandpopup import EditCommandPopup

from bot.utils import toast_notification, bot_launched_notification, \
    bot_stopped_notification, load_custom_commands, save_custom_commands


class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super(AuthScreen, self).__init__(**kwargs)
        self.session = App.get_running_app().session
        
    def on_enter(self):
        self.ids.pass_auth.disabled = not self.session.authorized

    def log_in(self, twofa_key=''):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login and password:
            authorized, error = self.session.authorization(
                                login=login, password=password, key=twofa_key
                                )
            if authorized:
                self.ids.pass_input.text = ''
                if twofa_key:
                    return True
                self.parent.show_home_screen()
            elif error:
                if 'code is needed' in error:
                    self.parent.show_twofa_screen()
                    return
                elif 'incorrect password' in error:
                    toast_notification(u'Неправильный логин или пароль')
                else:
                    toast_notification(error, length_long=True)
                    return
        self.ids.pass_input.text = ''


class TwoFAKeyEnterScreen(Screen):
    def twofa_auth(self):
        if self.ids.twofa_textinput.text:
            login_screen_widget = self.parent.get_screen('login_screen')
            if login_screen_widget.log_in(twofa_key=self.ids.twofa_textinput.text):
                self.parent.show_home_screen()
            else:
                toast_notification(u'Неправильный код подтверждения')
            self.ids.twofa_textinput.text = ''


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.bot_check_event = Clock.schedule_interval(self.check_if_bot_active, 1)
        self.session = App.get_running_app().session
        self.launch_bot_text = 'Включить бота'
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text

    @mainthread
    def on_main_btn_press(self):
        config = App.get_running_app().config

        if self.ids.main_btn.text == self.launch_bot_text:
            self.launch_bot(config)
        else:
            self.stop_bot(config)

    def launch_bot(self, config):
        self.activation_status = config.getdefault('General', 'bot_activated', 'False')
        use_custom_commands = config.getdefault('General', 'use_custom_commands', 'False')
        protect_custom_commands = config.getdefault('General', 'protect_cc', "True")

        while not self.session.launch_bot(
                    activated=self.activation_status == 'True',
                    use_custom_commands=use_custom_commands == 'True',
                    protect_custom_commands=protect_custom_commands == 'True'
                ):
            continue

        self.ids.main_btn.text = self.stop_bot_text
        self.bot_check_event()
        bot_launched_notification()

    def stop_bot(self, config):
        self.bot_check_event.cancel()
        bot_stopped = False

        while not bot_stopped:
            bot_stopped, new_activation_status = self.session.stop_bot()

        if new_activation_status != self.activation_status:
            config.set('General', 'bot_activated', str(new_activation_status))
            config.write()

        self.ids.main_btn.text = self.launch_bot_text
        bot_stopped_notification()

    def update_answers_count(self):
        self.ids.answers_count_lb.text = 'Ответов: {}'.format(self.session.reply_count)

    def logout(self):
        self.session.authorization(logout=True)
        self.parent.show_auth_screen()
    
    def check_if_bot_active(self, tick):
        self.update_answers_count()
        if self.ids.main_btn.text == self.stop_bot_text and\
                not self.session.running:
            self.bot_check_event.cancel()
            self.ids.main_btn.text = self.launch_bot_text
            bot_stopped_notification()

            if self.session.runtime_error:
                toast_notification(self.session.runtime_error, length_long=True)


class CustomCommandsScreen(Screen):
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.included_keys = []

    def leave(self):
        self.parent.show_home_screen()

    def on_enter(self):
        self.custom_commands = load_custom_commands()
        
        for key in sorted(self.custom_commands.keys()):
            if key not in self.included_keys and len(self.custom_commands[key]) == 1:
                block = CustomCommandBlock(command=key)
                self.ids.cc_list.add_widget(block)
                self.included_keys.append(key)
        Clock.schedule_once(self.update_commands_list_size, .1)

    def update_commands_list_size(self, delay):
        self.ids.cc_list.size_hint_y = None
        self.ids.cc_list.height = self.ids.cc_list.minimum_height

    def open_edit_popup(self, command, item):
        popup = EditCommandPopup(
            command_text=command,
            response_text=self.custom_commands[command][0],
            item=item
            )
        popup.ids.delete_command_btn.bind(
            on_press=lambda x: self.remove_command(
                popup.ids.command_text.text.decode('utf8'),
                item
                )
            )
        popup.ids.apply_btn.bind(
            on_press=lambda x: self.save_edited_command(
                popup.ids.command_text.text,
                popup.ids.response_text.text
            )
        )
        popup.open()

    def save_edited_command(self, command, response):
        self.custom_commands[command.decode('utf8')] = [response.decode('utf8')]
        save_custom_commands(self.custom_commands)

    def remove_command(self, command, item):
        self.custom_commands.pop(command, None)
        save_custom_commands(self.custom_commands)
        self.included_keys.remove(command)
        self.ids.cc_list.remove_widget(item)
        Clock.schedule_once(self.update_commands_list_size, .1)

    def add_command(self):
        pass


class Root(ScreenManager):
    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)
        self.transition = FadeTransition()

    def show_auth_screen(self):
        if not 'auth_screen' in self.screen_names:
            self.add_widget(AuthScreen())
        self.current = 'auth_screen'

    def show_twofa_screen(self):
        if not 'twofa_screen' in self.screen_names:
            self.add_widget(TwoFAKeyEnterScreen())
        self.current = 'twofa_screen'

    def show_home_screen(self):
        if not 'main_screen' in self.screen_names:
            self.add_widget(MainScreen())
        self.current = 'main_screen'

    def show_custom_commands_screen(self):
        if not 'cc_screen' in self.screen_names:
            self.add_widget(CustomCommandsScreen())
        self.current = 'cc_screen'