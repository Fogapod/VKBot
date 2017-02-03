__version__ = '0.1.0'
__author__ = 'Eugene Ershov - https://vk.com/fogapod'

from kivy.utils import platform

PATH = '/storage/emulated/0/Git/ChatBot_UI' if platform == 'android' else ''
DATA_PATH = 'data/'