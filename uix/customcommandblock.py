from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        self.command = ''
        self.responses = []
        self.dropdown = kwargs['dropdown']


class ListDropDown(DropDown):
	def __init__(self, **kwargs):
		super(ListDropDown, self).__init__(**kwargs)
		self.container.spacing = self.required_spacing


class CommandButton(Button):
    pass
