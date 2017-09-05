# coding:utf8


from kivy.uix.popup import Popup


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