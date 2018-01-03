# coding:utf8


LANG_CODES = {
    'c#': 1,
    'vb.net': 2,
    'f#': 3,
    'java': 4,
    'python2': 5,
    'py2': 5,
    'c': 6,  # gcc
    'c++': 7,  # gcc
    'php': 8,
    'pascal': 9,
    'objective-c': 10,
    'haskell': 11,
    'ruby': 12,
    'perl': 13,
    'lua': 14,
    'nasm': 15,
    'sql-server': 16,
    'javascript': 17,
    'lisp': 18,
    'prolog': 19,
    'go': 20,
    'scala': 21,
    'scheme': 22,
    'node.js': 23,
    'python3': 24,
    'py3': 24,
    'python': 24,
    'py': 24,
    'octave': 25,
    'c (clang)': 26,
    'c++ (clang)': 27,
    'c++ (vc++)': 28,
    'c (vc)': 29,
    'd': 30,
    'r': 31,
    'tcl': 32,
    'mysql': 33,
    'postgresql': 34,
    'oracle': 35,
    'swift': 37,
    'bash': 38,
    'ada': 39,
    'erlang': 40,
    'elixir': 41,
    'ocaml': 42,
    'kotlin': 43,
    'brainfuck': 44,
    'bf': 44,
    'fortran': 45
}

class Plugin(object):
    __doc__ = """Плагин предназначен для выполнения кода сервисом rextester.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword} <язык> <программа>
    Пример: {keyword} python print('Hello rex!')
    Показать список доступных языков: {keyword} <list|список>"""

    name = 'rex'
    keywords = (name, )
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, utils, *args, **kwargs):
        params = {
            'LanguageChoice': 24,
            'Program': '',
            'CompilerArgs': ''
        }

        if msg.args[1] in ('list', u'список'):
            for k, v in sorted(LANG_CODES.items(), key=lambda x: x[1]):
                rsp.text += '{0}: {1}\n'.format(v, k)
            return rsp

        if len(msg.args) < 3:
            rsp.text = u'Недостаточно аргументов'
            return rsp

        if msg.args[1].isdigit():
            params['LanguageChoice'] = int(msg.args[1])
        else:
            params['LanguageChoice'] = LANG_CODES.get(msg.args[1].lower(), '')

            if not params['LanguageChoice']:
                rsp.text = u'Неверно указан язык'
                return rsp

        if params['LanguageChoice'] in (6, 26):
            params['CompilerArgs'] = 'source_file.c -o a.out'
        elif params['LanguageChoice'] == 29:
            params['CompilerArgs'] = 'source_file.c -o a.exe'
        elif params['LanguageChoice'] in (7, 27):
            params['CompilerArgs'] = 'source_file.cpp -o a.out'
        elif params['LanguageChoice'] == 28:
            params['CompilerArgs'] = 'source_file.cpp -o a.exe'

        params['Program'] = ' '.join(msg.args[2:])

        result, error = utils.vkr.http_r_post('http://rextester.com/rundotnet/api',
                                                                    params=params)
        if error:
            rsp.text = error
            return rsp

        result_json = result.json()

        rsp.text = \
            result_json['Errors'] or result_json['Result'] or result_json['Stats']
        
        rsp.text = rsp.text.strip()

        return rsp
