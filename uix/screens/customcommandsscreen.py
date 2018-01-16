# coding:utf8


from kivy.app import App
from kivy.clock import mainthread, Clock
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from uix.popups.editcommandpopup import EditCommandPopup
from uix.widgets import ColoredScreen

from bot import utils

MAX_COMMAND_PREVIEW_TEXT_LEN = 47


class ListButton(Button):

    def preview(self, text):
        prewiew = text.replace('\n', '  ')

        if len(prewiew) > MAX_COMMAND_PREVIEW_TEXT_LEN:
            return prewiew[:MAX_COMMAND_PREVIEW_TEXT_LEN] + '...'
        return prewiew


class Command(ListButton):

    def on_release(self):
        if len(self.responses) == 1:
            self.edit_popup.open_command(self.command_text, self.responses[0][0],
                                         self.responses[0][1:],
                                         self.index_in_list, self.command_list)
        else:
            if self.dropdown is None:
                self.dropdown = DropDown()

                for item in sorted(self.responses):
                    self.dropdown.add_widget(Response(self, item))

            self.dropdown.open(self)

    def on_long_release(self):
        # TODO: open dropdown with "+" at the end
        pass


class Response(ListButton):

    def __init__(self, command, item, **kwargs):
        super(ListButton, self).__init__(**kwargs)
        self.command_text = command.command_text
        self.command_list = command.command_list
        self.command_index_in_list = command.index_in_list
        self.edit_popup = command.edit_popup
        self.response_text = item[0]
        self.options = item[1:]

    def on_release(self):
        self.edit_popup.open_command(self.command_text, self.response_text,
                                     self.options, self.command_index_in_list,
                                     self.command_list)


class CustomCommandsScreen(ColoredScreen):

    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.current_page_num = 0
        self.num_pages = 10

        self.update_page_label()
        self.update_l_r_buttons_state()

        self.edit_popup = EditCommandPopup()
        self.edit_popup.setup()

    def on_enter(self):
        self.sort()

    def next_page(self):
        self.current_page_num += 1
        self.update_page_label()
        self.update_l_r_buttons_state()

    def prev_page(self):
        self.current_page_num -= 1
        self.update_page_label()
        self.update_l_r_buttons_state() 

    def update_page_label(self):
        self.ids.page_label.text = \
            '%d [%d]' % (self.current_page_num + 1, self.num_pages)

    def update_l_r_buttons_state(self):
        if self.current_page_num == self.num_pages - 1:
            self.ids.button_right.disabled = True
        elif self.current_page_num == 0:
            self.ids.button_left.disabled = True
        else:
            self.ids.button_right.disabled = False
            self.ids.button_left.disabled  = False

    def leave(self):
        self.parent.go_back()

    def read_custom_commands(self):
        self.custom_commands = utils.load_custom_commands()

        if not self.custom_commands and type(self.custom_commands) is not dict:
            utils.toast_notification(u'Повреждён файл пользовательских команд')
            self.leave()

    def sort(self):
        self.read_custom_commands()

        App.get_running_app().open_loading_popup()
        Clock.schedule_once(self._sort)

    def _sort(self, dt):
        self.ids.command_list.data = []

        for i, name in enumerate(sorted(self.custom_commands)):
            self.ids.command_list.data.append(
                {
                    'command_text': name,
                    'responses': self.custom_commands[name],
                    'command_list': self.ids.command_list.data,
                    'index_in_list': i,
                    'edit_popup': self.edit_popup
                }
            )

        App.get_running_app().close_loading_popup()