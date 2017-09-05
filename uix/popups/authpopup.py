# coding:utf8


from kivy.uix.modalview import ModalView


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