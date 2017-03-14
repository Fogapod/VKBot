__all__ = ('toast')

_toast = None

def _get_ref():
    global _toast
    if _toast is None:
        try:
            import android
        except ImportError:
            from kivytoast import toast
        else:
            from androidtoast import toast

        _toast = toast
    return _toast

def toast(text, length_long=False):
    _get_ref()(text, length_long=length_long)
