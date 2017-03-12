from kivy import platform

__all__ = ('toast')

_toast = None

def _get_ref():
    global _toast
    if _toast is None:
        if platform == 'android': 
            from androidtoast import toast
        else:
            from kivytoast import toast
        _toast = toast
    return _toast

def toast(text, length_long=False):
    _get_ref()(text, length_long=length_long)
