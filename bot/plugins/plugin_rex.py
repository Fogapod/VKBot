# coding:utf8


LANG_CODES = {
    'c#': 1,
    'vb.net': 2,
    'visualbasic': 2,
    'f#': 3,
    'java': 4,
    'python2': 5,
    'py2': 5,
    'c': 6,
    'c(gcc)': 6,
    'c++': 7,
    'cpp': 7,
    'c++(gcc)': 7,
    'php': 8,
    'pascal': 9,
    'objective-c': 10,
    'oc': 10,
    'haskell': 11,
    'hs': 11,
    'ruby': 12,
    'rb': 12,
    'perl': 13,
    'lua': 14,
    'nasm': 15,
    'sqlserver': 16,
    'javascript': 17,
    'js': 17,
    'lisp': 18,
    'prolog': 19,
    'go': 20,
    'scala': 21,
    'scheme': 22,
    'nodejs': 23,
    'node': 23,
    'python3': 24,
    'py3': 24,
    'python': 24,
    'py': 24,
    'octave': 25,
    'c(clang)': 26,
    'c++(clang)': 27,
    'c++(vc++)': 28,
    'c(vc)': 29,
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
    'fortran': 45,
    'ft': 45
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
            last_code = 0
            for k, v in sorted(LANG_CODES.items(), key=lambda x: x[1]):
                if v == last_code:
                    rsp.text += ', ' + k
                else:
                    rsp.text += '\n{0}: {1}'.format(v, k)
                    last_code = v

            rsp.text = rsp.text.strip()
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

        if params['LanguageChoice'] in (6, 26):  # c (gcc, clang)
            params['CompilerArgs'] = '-Wall -std=gnu99 -O2 -o a.out source_file.c'
        elif params['LanguageChoice'] == 29:  # c (vc)
            params['CompilerArgs'] = 'source_file.c -o a.exe'
        elif params['LanguageChoice'] == 7:  # c++ (gcc)
            params['CompilerArgs'] = '-Wall -std=c++14 -O2 -o a.out source_file.cpp'
        elif params['LanguageChoice'] == 27:  # c++ (clang)
            params['CompilerArgs'] = '-Wall -std=c++14 -stdlib=libc++ -O2 -o a.out source_file.cpp'
        elif params['LanguageChoice'] == 28:  # c++ (vc++)
            params['CompilerArgs'] = 'source_file.cpp -o a.exe /EHsc /MD /I C:\boost_1_60_0 /link /LIBPATH:C:\boost_1_60_0\stage\lib'
        elif params['LanguageChoice'] == 30:  # d
            params['CompilerArgs'] = 'source_file.d -ofa.out'
        elif params['LanguageChoice'] == 20:  # go
            params['CompilerArgs'] = '-o a.out source_file.go'
        elif params['LanguageChoice'] == 11:  # haskhell
            params['CompilerArgs'] = '-o a.out source_file.hs'
        elif params['LanguageChoice'] == 10:  # objective-c
            params['CompilerArgs'] = '-MMD -MP -DGNUSTEP -DGNUSTEP_BASE_LIBRARY=1 -DGNU_GUI_LIBRARY=1 -DGNU_RUNTIME=1 -DGNUSTEP_BASE_LIBRARY=1 -fno-strict-aliasing -fexceptions -fobjc-exceptions -D_NATIVE_OBJC_EXCEPTIONS -pthread -fPIC -Wall -DGSWARN -DGSDIAGNOSE -Wno-import -g -O2 -fgnu-runtime -fconstant-string-class=NSConstantString -I. -I /usr/include/GNUstep -I/usr/include/GNUstep -o a.out source_file.m -lobjc -lgnustep-base'

        params['Program'] = ' '.join(msg.args[2:])

        result, error = utils.vkr.http_r_post('http://rextester.com/rundotnet/api',
                                                                    params=params)
        if error:
            rsp.text = error
            return rsp

        result_json = result.json()

        rsp.text = result_json['Errors'] or result_json['Result']

        rsp.text = rsp.text.strip()

        if not rsp.text:
            rsp.text = 'Empty output'

        return rsp
