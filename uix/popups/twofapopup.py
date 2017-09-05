# coding:utf8


from kivy.uix.modalview import ModalView

from kivy.core.clipboard import Clipboard


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