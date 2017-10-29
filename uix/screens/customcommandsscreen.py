# coding:utf8


from kivy.app import App
from kivy.clock import mainthread, Clock

from uix.popups.editcommandpopup import EditCommandPopup
from uix.widgets import ColoredScreen, CustomCommandBlock, ListDropDown, \
    CommandButton

from bot import utils


class CustomCommandsScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.edit_popup = EditCommandPopup()
        self.included_keys = []
        self.max_command_preview_text_len = 47


    def on_enter(self):
        App.get_running_app().open_loading_popup()
        Clock.schedule_once(self.sort_blocks)

    def sort_blocks(self, *args):
        for widget in sorted(self.ids.cc_list.children):
            self.included_keys.remove(widget.command)
            self.ids.cc_list.remove_widget(widget)

        self.custom_commands = utils.load_custom_commands()

        if not self.custom_commands and type(self.custom_commands) is not dict:
            utils.toast_notification(u'Повреждён файл пользовательских команд')
            Clock.schedule_once(self.leave, .1)

        else:
            for key in sorted(self.custom_commands.keys()):
                for item in sorted(self.custom_commands[key]):
                    if type(item) is not list or len(item) \
                            < utils.CUSTOM_COMMAND_OPTIONS_COUNT + 1:
                        self.custom_commands[key].remove(item)
                        if type(item) is not list:
                            item = [item]
                        while len(item) < utils.CUSTOM_COMMAND_OPTIONS_COUNT + 1:
                            item.append(0)
                        self.custom_commands[key].append(item)
                        utils.save_custom_commands(self.custom_commands)

                self.custom_commands[key] = sorted(
                    self.custom_commands[key], key=lambda x: x[0])
                if key not in self.included_keys:
                    self.add_command(key, self.custom_commands[key])

        App.get_running_app().close_loading_popup()


    def leave(self, delay=None):
        self.parent.show_main_screen()


    def open_edit_popup(self, command_button, command_block):
        max_title_len = 27
        title = command_button.command.replace('\n', '  ')
        if len(title) > max_title_len:
            title = title[:max_title_len] + '...'

        self.edit_popup.command_block = command_block
        self.edit_popup.switch_command(
            command_button,
            title=u'Настройка команды «{}»'.format(title)
            )

        self.edit_popup.ids.delete_command_btn.unbind(
            on_release=self.edit_popup.ids.delete_command_btn._callback
            )
        self.edit_popup.ids.apply_btn.unbind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )

        new_delete_callback = lambda x: self.remove_command(
            command_button.command, command_button.response,
            command_button, self.edit_popup.command_block
            )
        new_save_callback = lambda x: self.save_edited_command(
            self.edit_popup.ids.command_textinput.text,
            self.edit_popup.ids.response_textinput.text,
            command_button, self.edit_popup.command_block
            )

        self.edit_popup.ids.delete_command_btn._callback = new_delete_callback
        self.edit_popup.ids.apply_btn._callback = new_save_callback

        self.edit_popup.ids.delete_command_btn.bind(
            on_release=self.edit_popup.ids.delete_command_btn._callback
            )
        self.edit_popup.ids.apply_btn.bind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )

        self.edit_popup.open()


    def open_new_command_popup(self):
        self.edit_popup.switch_to_empty_command()
        self.edit_popup.command_block = None

        create_callback = lambda x: self.create_command(
            self.edit_popup.ids.command_textinput.text,
            self.edit_popup.ids.response_textinput.text,
            )
        self.edit_popup.ids.apply_btn._callback = create_callback

        self.edit_popup.ids.apply_btn.bind(
            on_release=self.edit_popup.ids.apply_btn._callback
            )
        self.edit_popup.open()


    def save_edited_command(self, command, response, command_button, block):
        if not self.edit_popup.ids.command_textinput.text:
            utils.toast_notification(u'Поле для команды не может быть пустым')
            return

        options = self.edit_popup.get_options()

        button_command = command_button.command

        if options != command_button.options:
            self.custom_commands[button_command].remove(
                [command_button.response] + command_button.options)
            self.custom_commands[button_command].append(
                [command_button.response] + options)

            command_button.options = options[:]

            for r in self.custom_commands[button_command]:
                r[1] = options[0]

            for button in block.dropdown.container.children:
                button.options[0] = options[0]

        if button_command != command:
            if command in self.included_keys:
                utils.toast_notification(u'Такая команда уже существует')
                return

            self.included_keys.remove(button_command)
            self.included_keys.append(command)
            command_button.command = command
            block.command = command
            if len(block.responses) > 1:
                for button in block.dropdown.container.children:
                    button.command = command

            command_preview = command
            command_preview = command_preview.replace('\n', '  ')
            if len(command_preview) > self.max_command_preview_text_len:
                command_preview = \
                    command_preview[:self.max_command_preview_text_len] + '...'
            block.ids.dropdown_btn.text = command_preview

            self.custom_commands[command] = []
            for r in self.custom_commands[button_command]:
                self.custom_commands[command].append(r)
            self.custom_commands.pop(button_command)

        if response != command_button.response:
            self.custom_commands[command].remove(
                [command_button.response] + command_button.options)
            block.responses.remove(command_button.response)

            command_button.response = response

            response_preview = response
            response_preview = response_preview.replace('\n', '  ')

            if len(response_preview) > self.max_command_preview_text_len:
                response_preview = \
                    response_preview[:self.max_command_preview_text_len] + '...'

            if response_preview == '':
                response_preview = ' '

            command_button.text = response_preview

            block.responses.append(response)

            command_preview = command
            command_preview = command_preview.replace('\n', '  ')

            if len(command_preview) > self.max_command_preview_text_len:
                command_preview = \
                    command_preview[:self.max_command_preview_text_len] + '...'

            block.ids.dropdown_btn.text = command_preview

            self.custom_commands[command].append([response] + options)

        utils.save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()


    def remove_command(self, command, response, command_button, block):
        options = self.edit_popup.get_options()

        if len(block.responses) == 1:
            self.custom_commands.pop(command, None)
            self.included_keys.remove(command)
            self.ids.cc_list.remove_widget(block)
        elif len(block.responses) == 2:
            block.ids.dropdown_btn.unbind(
                on_release=block.ids.dropdown_btn.callback)
            block.dropdown.remove_widget(command_button)

            command_button = block.ids.dropdown_btn
            command_button.command = command
            command_button.response =\
                block.dropdown.container.children[0].response # last child
            block.dropdown.remove_widget(block.dropdown.container.children[0])

            command_button.options = self.custom_commands[command][0][1:]

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)
            block.responses.remove(response)

            self.custom_commands[command].remove(
                [response] + options)

            block.dropdown.dismiss()
        else:
            self.custom_commands[command].remove(
                [response] + options)
            block.dropdown.remove_widget(command_button)
            block.responses.remove(response)
            block.dropdown.dismiss()

        utils.save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()


    def create_command(self, command, response):
        if not self.edit_popup.ids.command_textinput.text:
            utils.toast_notification(u'Поле для команды не может быть пустым')
            return

        options = self.edit_popup.get_options()

        if command not in self.included_keys:
            self.custom_commands[command] = [[response] + options]
            self.add_command(command, [[response] + options])
        else:
            for child in self.ids.cc_list.children:
                if child.command == command:
                    block = child
                    break

            if len(self.custom_commands[command]) == 1:
                old_command_button = CommandButton(
                    text=block.ids.dropdown_btn.response)
                old_command_button.command = block.ids.dropdown_btn.command
                old_command_button.response = block.ids.dropdown_btn.response
                del block.ids.dropdown_btn.command
                del block.ids.dropdown_btn.response

                old_command_button.options = block.ids.dropdown_btn.options

                callback = lambda x: self.open_edit_popup(x, block)
                old_command_button.callback = callback
                old_command_button.bind(on_release=old_command_button.callback)

                block.ids.dropdown_btn.unbind(
                    on_release=block.ids.dropdown_btn.callback)
                dropdown_callback = block.dropdown.open
                block.ids.dropdown_btn.callback = dropdown_callback
                block.ids.dropdown_btn.bind(
                    on_release=block.ids.dropdown_btn.callback)

                block.dropdown.add_widget(old_command_button)

            response_preview = response
            response_preview = response_preview.replace('\n', '  ')

            if len(response_preview) > self.max_command_preview_text_len:
                response_preview = \
                    response_preview[:self.max_command_preview_text_len] + '...'

            if response_preview == '':
                response_preview = ' '

            command_button = CommandButton(text=response_preview)
            command_button.command = command
            command_button.response = response
            command_button.options = options

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            block.dropdown.add_widget(command_button)
            block.responses.append(response)

            self.custom_commands[command].append([response] + options)

            for r in self.custom_commands[command]:
                r[1] = options[0]

            for button in block.dropdown.container.children:
                button.options[0] = options[0]

        utils.save_custom_commands(self.custom_commands)
        self.edit_popup.dismiss()


    def add_command(self, command, response):
        dropdown = ListDropDown()
        block = CustomCommandBlock(dropdown=dropdown)
        
        for item in response:
            if len(response) > 1:
                response_preview = item[0]
                response_preview = response_preview.replace('\n', '  ')

                if len(response_preview) > self.max_command_preview_text_len:
                    response_preview = \
                        response_preview[:self.max_command_preview_text_len] + '...'
                if response_preview == '':
                    response_preview = ' '

                command_button = CommandButton(text=response_preview)
            else:
                command_button = block.ids.dropdown_btn

            command_button.command = command
            command_button.response = item[0]
            command_button.options = item[1:]

            callback = lambda x: self.open_edit_popup(x, block)
            command_button.callback = callback
            command_button.bind(on_release=command_button.callback)

            if len(response) > 1:
                block.dropdown.add_widget(command_button)

            block.responses.append(item[0])

        block.command = command

        command_preview = command
        command_preview = command_preview.replace('\n', '  ')

        if len(command_preview) > self.max_command_preview_text_len:
            command_preview = \
                command_preview[:self.max_command_preview_text_len] + '...'

        block.ids.dropdown_btn.text = command_preview

        if len(response) > 1:
            dropdown_callback = block.dropdown.open
            block.ids.dropdown_btn.callback = dropdown_callback
            block.ids.dropdown_btn.bind(
                on_release=block.ids.dropdown_btn.callback)
        self.ids.cc_list.add_widget(block)
        self.included_keys.append(command)