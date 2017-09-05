from kivy.uix.modalview import ModalView


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