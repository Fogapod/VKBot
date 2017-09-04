# coding:utf8


from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView

from kivy.core.clipboard import Clipboard
from kivy.properties import NumericProperty
from kivy.animation import Animation


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


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.options = [0, 0, 0, 0, 0]
        self.command_block = None


    def switch_command(self, command_button, title):
        self.title = title
        self.ids.command_textinput.text = command_button.command
        self.ids.response_textinput.text = command_button.response
        self.options = command_button.options[:]

        self.switch_option_state(self.ids.regex_btn,
                                 self.ids.regex_btn.states,
                                 force_state=self.options[0])

        self.switch_option_state(self.ids.force_unmark_btn,
                                 self.ids.force_unmark_btn.states,
                                 force_state=self.options[1])
        
        self.switch_option_state(self.ids.force_forward_btn,
                                 self.ids.force_forward_btn.states,
                                 force_state=self.options[2])

        self.switch_option_state(self.ids.appeal_only_btn,
                                 self.ids.appeal_only_btn.states,
                                 force_state=self.options[3])

        self.switch_option_state(self.ids.disable_btn,
                                 self.ids.disable_btn.states,
                                 force_state=self.options[4])

        self.ids.delete_command_btn.disabled = False


    def switch_to_empty_command(self):
        self.title = u'Настройка новой команды'
        self.ids.command_textinput.text = ''
        self.ids.response_textinput.text = ''

        self.switch_option_state(self.ids.regex_btn,
                                 self.ids.regex_btn.states,
                                 force_state=0)

        self.switch_option_state(self.ids.force_unmark_btn,
                                 self.ids.force_unmark_btn.states,
                                 force_state=0)
        
        self.switch_option_state(self.ids.force_forward_btn,
                                 self.ids.force_forward_btn.states,
                                 force_state=0)

        self.switch_option_state(self.ids.appeal_only_btn,
                                 self.ids.appeal_only_btn.states,
                                 force_state=0)

        self.switch_option_state(self.ids.disable_btn,
                                 self.ids.disable_btn.states,
                                 force_state=0)

        self.options = [0, 0, 0, 0, 0]
        self.command_block = None

        if self.ids.delete_command_btn._callback:
            self.ids.delete_command_btn.unbind(
                on_release=self.ids.delete_command_btn._callback
                )

        if self.ids.apply_btn._callback:
            self.ids.apply_btn.unbind(
                on_release=self.ids.apply_btn._callback
                )

        self.ids.delete_command_btn.disabled = True


    def get_options(self):
        return self.options


    def switch_option_state(self, option_button, states, force_state=None):
        if force_state is not None:
            option_button.current_state = force_state
        elif option_button.current_state >= states[-1]:
            option_button.current_state = states[0]
        elif len(states) == 2:
            option_button.current_state = states[1]
        else:
            option_button.current_state += 1
        
        if option_button.current_state == 0:
            option_button.background_color = [1, 0, 0, .6]
        elif option_button.current_state == 1:
            option_button.background_color = [0, 0, 1, .6]
        elif option_button.current_state == 2:
            option_button.background_color = [0, 1, 0, .6]

        if option_button.text == 'G':
            self.ids.command_textinput.lower_mode = \
                option_button.current_state == 0
            self.options[0] = option_button.current_state
        elif option_button.text == 'F':
            self.options[1] = option_button.current_state
        elif option_button.text == 'M':
            self.options[2] = option_button.current_state
        elif option_button.text == 'A':
            self.options[3] = option_button.current_state
        elif option_button.text == 'D':
            self.options[4] = option_button.current_state
