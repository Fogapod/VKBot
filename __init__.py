__version__ = '0.1.0'
__author_vk_id__ = 180850898
__author__ = 'Eugene Ershov - https://vk.com/id%d' % __author_vk_id__

from kivy import platform

PATH = '/sdcard/VKBot/' if platform == 'android' else ''
DATA_PATH = 'data/'