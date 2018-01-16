# coding:utf8


from kivy.uix.popup import Popup

from uix.widgets import FontelloButton

class EditCommandPopup(Popup):

    def setup(self):
        self.command_list = None
        self.command_index_in_list = None
        self.options = [0, 0, 0, 0, 0]

        self.ids.delete_command_btn.disabled = True

    def open_empty(self):
        self.setup()
        self._switch_option_states()

        self.title = u'Настройка новой команды'
        self.ids.command_textinput.text = ''
        self.ids.response_textinput.text = ''

        self.open()

    def open_command(self, command_text, response_text, options, index_in_list,
                     command_list): 
        max_title_len = 49  # TODO: remove magic number
        preview = u'Настройка команды «%s»' % command_text
        preview = preview.replace('\n', '  ')

        if len(preview) > max_title_len:
           preview = preview[:max_title_len] + '...'

        self.title = preview
        self.ids.command_textinput.text = command_text
        self.ids.response_textinput.text = response_text

        self.command_index_in_list = index_in_list
        self.options = options

        self._switch_option_states()
        self.ids.delete_command_btn.disabled = False

        self.open()

    def save_command(self):
        self.dismiss()

    def delete_command(self):
        if len(self.command.responses) == 1:
            self.command_list.pop(self.command_index_in_list)

        self.dismiss()

    def _switch_option_states(self):
        self._switch_option_state(self.ids.regex_btn,
                                  self.ids.regex_btn.states,
                                  force_state=self.options[0])

        self._switch_option_state(self.ids.force_unmark_btn,
                                  self.ids.force_unmark_btn.states,
                                  force_state=self.options[1])
        
        self._switch_option_state(self.ids.force_forward_btn,
                                  self.ids.force_forward_btn.states,
                                  force_state=self.options[2])

        self._switch_option_state(self.ids.appeal_only_btn,
                                  self.ids.appeal_only_btn.states,
                                  force_state=self.options[3])

        self._switch_option_state(self.ids.disable_btn,
                                  self.ids.disable_btn.states,
                                  force_state=self.options[4])

    def _switch_option_state(self, option_button, states, force_state=None):
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


class OptionButton(FontelloButton):

    def __init__(self, **kwargs):
        self.states = (0, 1, 2)
        self.colors_by_state = ((1, 0, 0, .6), (0, 0, 1, .6), (0, 1, 0, .6))
        super(OptionButton, self).__init__(**kwargs)
        self.current_state = self.states[0]
        self.background_color = self.colors_by_state[self.current_state]

    def switch_state_to(self, state):
        self.current_state = state
        self.background_color = self.colors_by_state[state]

    def next_state(self):
        if self.current_state >= self.states[-1]:
            self.current_state = self.states[0]
        elif len(self.states) == 2:
            self.current_state = self.states[1]
        else:
            self.current_state += 1

        self.background_color = self.colors_by_state[self.current_state]
        self.ids.root_popup.options[self.option_number] = self.current_state
        if self.option_number == 0:  # regex
             self.ids.command_textinput.lower_mode = self.current_state == 0