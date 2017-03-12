'''
Fasades
=======

Interface of all the features available.

'''

__all__ = ('Accelerometer', 'Audio', 'Battery', 'Call', 'Camera', 'Compass',
           'Email', 'FileChooser', 'GPS', 'Gyroscope', 'IrBlaster',
           'Orientation', 'Notification', 'Sms', 'TTS', 'UniqueID', 'Vibrator',
           'Wifi', 'Flash')

from accelerometer import Accelerometer
from audio import Audio
from battery import Battery
from call import Call
from camera import Camera
from compass import Compass
from email import Email
from filechooser import FileChooser
from gps import GPS
from gyroscope import Gyroscope
from irblaster import IrBlaster
from orientation import Orientation
from notification import Notification
from sms import Sms
from tts import TTS
from uniqueid import UniqueID
from vibrator import Vibrator
from flash import Flash
from wifi import Wifi
