from kivy.uix.popup import Popup


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.ids.command_text.text = kwargs['command_text']
        self.ids.response_text.text = kwargs['response_text']

        self.switch_option_state(self.ids.regex_btn,
                                 self.ids.regex_btn.states,
                                 force_state=kwargs['use_regex'])

        self.switch_option_state(self.ids.force_unmark_btn,
                                 self.ids.force_unmark_btn.states,
                                 force_state=kwargs['force_unmark'])
        
        self.switch_option_state(self.ids.force_forward_btn,
        	                        self.ids.force_forward_btn.states,
        	                        force_state=kwargs['force_forward'])

        self.switch_option_state(self.ids.appeal_only_btn,
                                 self.ids.appeal_only_btn.states,
                                 force_state=kwargs['appeal_only'])

        self.switch_option_state(self.ids.disable_btn,
        	                        self.ids.disable_btn.states,
        	                        force_state=kwargs['disable'])

        self.command_block = kwargs['command_block']
        self.command_button = kwargs['command_button']
        if not self.command_button:
            self.ids.delete_command_btn.disabled = True


    def switch_command(self, **kwargs):
        pass


    def switch_option_state(self, option_button, states, force_state=None):
        if force_state is not None:
            option_button.current_state = force_state
        elif option_button.current_state == states[-1]:
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
