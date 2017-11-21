# Плагины
VKBot поддерживает плагины, написанные на python.  
Все встроенные команды реализованы через плагины. Для добавления плагина, его необходимо назвать его по образцу: `plugin_длинное_название.py`.  
Если плагин назван неправильно, он не будет загружен.  
При необходимости, можно заменить встроенный плагин на свой, указав такое же имя плагина (не путать с именем файла!)

## Базовый палгин
```python
# coding:utf8


class Plugin(object):
    __doc__ = '''Плагин предназначен для ответа на команду.
    Для использования необходимо иметь уровень доступа {protection} или выше
    Ключевые слова: [{keywords}]
    Использование: {keyword}
    Пример: {keyword}'''

    name = 'plugin'
    keywords = (name, u'плагин')
    protection = 0
    argument_required = False

    def respond(self, msg, rsp, *args, **kwargs):
        # ваш код
        # ...
        rsp.text = u'Результат работы'

        return rsp
```

## Базовая структура плагина
Плагину необходимо иметь следующие элементы (в соответствующем порядке):
* основной класс с названием `Plugin`, к которому будет обращаться программа
* документацию
* переменную `name`, содержащую имя плагина
* переменную `keywords`, содержащую ключевые слова для вызова плагина
* переменную `protection`
* переменную `argument_required`, обозначающую, нужно ли передавать дополнительный аргумент для работы команды
* функцию `respond`

## Документация плагина
Класс плагина должен иметь переменную `__doc__`.  
Рекомендация по структуре строки документации:  
1 строка: `Плагин предназначен для <предназначение>.`  
2 строка: `    Для использования необходимо иметь уровень доступа {protection} или выше`  
3 строка: `    Ключевые слова: [{keywords}]`  
4 строкк: `    Использование: {keyword} <использование>`  
5 строка: `    Пример: {keyword} <пример>`  

*Необходимо указать свои значения вместо объектов в угловых скобках `<>`  

**Если плагин не предназначен для прямого вызова, 3, 4 и 5 строки должны иметь вид:  
`    Ключевые слова: -`  
`    Использование: -`  
`    Пример: -`  

## Переменные плагина

### name: str
Имя плагина

### keywords: tuple of str
Список клбчевых слов, при обнаружении которых будет вызван плагин

### protection: int
Если уровень доступа пользователь меньше (вызывается после функции _accept_request), команда не будет вызвана

### argument_required: bool
Если `True` и команде не передан дополнительный аргумент, функция `respond` не будет вызвана (функция `_accept_request` вызывается)

### disabled: bool
Если `True`, плагин не будет загружен. По умолчанию `False`

### priority: int
Чем выше значение, тем раньше плагин будет вызван. По умолчанию 0

## Функции плагина

### _accept_request(self, msg, rsp, utils, *args, **kwargs): bool
Вызывается до функции `respond`, возвращаемое значение определяет, будет ли вызван данный плагин. Определена по умолчанию:
```python
def _accept_request(self, msg, rsp, utils, *args, **kwargs):
    if msg.was_appeal and msg.args[0].lower() in self.keywords:
        return True

    return False
```
Обратите внимание: функция вызывается до проверки уровня доступа пользлвателя

### respond(self, msg, rsp, utils, *args, **kwargs): rsp
Принимает на вход объект сообщения msg, объект ответа rsp, объект класса дополнительных инструментов utils. (если не используется, можно не указывать явно:
`def respond(self, msg, rsp, *args, **kwargs):`  
Описание передаваемых объектов приводится ниже.  

Возвращает полученный объект ответа `rsp`

## Описание передаваемых объектов

### msg

Объект, сообщения, имеющий следующие переменные:
 
#### raw_text: str
Текст полученного сообщения (без изменений)

#### lower_text: str
`raw_text` в нижнем регистре

#### text: str
`raw_text` с вырезанным обращением(если было)

#### args: tuple of str
Список слов из `raw_text` (разделён пробелами)

#### was_appeal: bool
`True`, если было оращение к боту

#### from_user: bool
`True`, если сообщение пришло от пользователя

#### from_chat: bool
`True`, если сообщение пришло из беседы

#### from_group: bool
`True`, если сообщение пришло от группы

#### user_id: int
id диалога с пользователем (если `from_user`)

#### real_user_id: int
id автора сообщения (если `from_user` или `from_chat`)

#### chat_id: int
id беседы, из которой пришло сообщение (если `from_chat`)

#### chat_users: list of int
Список id пользователей беседы (если `from_chat`)

#### chat_name: str
Название беседы (если `from_chat`)

#### out: bool
`True`, если сообщение отправлено со страницы владельца бота

#### event_user_id: int
Поле `action_mid` полученного сообщения

#### event_text: str
Поле `action_text` полученного сообщения

#### msg_id: int
id полученного сообщения

***

### rsp
Объект ответа, имеющий следующие переменные:

#### target: int
Сообщение будет отправлено на этот id

#### sticker: int
id стикера, который необзодимо прикрепить

#### text: str
Текст сообщения, который необходимо отправить

#### do_mark: bool
Если `True`, сообщение будет отмечено (в соответствии с соответствующей опцией)

#### forward_msg: int
id сообщения, которое необходимо переслать


#### send():
Функция позволяет моментально отправить сообщение с текущими параметрами

***

### utils
Объект, содержащий вспомогательные функции и переменные:

#### get_settings(): dict
Возвращает словарь с настройками бота. Структура словаря на данный момент:

```python
{
    'appeals': tuple of str,
    'bot_name': str,
    'mark_type': str,
    'stable_mode': bool,
    'use_custom_commands': bool,
    'openweathermap_api_key': str
}
```

#### get_blacklist(): dict
Возращает словарь заблокированных id: `{id(str): 'Причина'}`

#### get_whitelist(): dict
Возвращает словарь id с повышенным доступом `{id(str): уровень(int)}`

#### get_custom_commands(): dict
Возвращает словарь пользовательских команд. Структура словаря:

```python
{
    'команда 1':
        ['ответ 1', 0, 0, 0, 0, 0],
        ['ответ 2', 0, 0, 0, 0, 0]
    'команда 2':
        ...
}

# 2-6 элементы ответа - опции, стоящие в позиции 0, 1 или 2
(1 существует не для всех)
```

#### save_setting(key, val, section='General'):
Функция сохраняет настройку `key` со значением `val` в секции конфига `General`

#### save_blacklist(blacklist):
Функия сохраняет словарь id с повышенным доступом (структура описана выше)

#### save_whitelist(whitelist):
Функия сохраняет словарь заблокированных id (структура описана выше)

#### save_custom_commands(custom_commands):
Функия сохраняет словарь пользовательских команд (структура описана выше)

#### clear_message_queue():
Функция заставляет бота забыть пришедшие к нему сообщения (если такие были)

#### get_user_access_level(msg): int
Возвращает уровень доступа пользователя

#### safe_format(text, *args, **kwargs): str
Функция форматирует строку, пропуская отсутствующие ключи

#### get_plugin_list(): list of str
Возвращает список загруженных плагинов (отсортированы в порядке приоритета)

#### get_builtin_plugin_list(): list of str
Возвращает список загруженных встроенных плагинов (не отсортированы)

#### get_custom_plugin_list(): list of str
Возвращает список загруженных пользовательских плагинов (не отсортированы)

#### get_plugin(name): plugin object
Возвращает объект плагина по имени

#### stop_bot():
Останавливает бота (сначала будет отправлено сообщение, возвращённое функцией `respond`)

#### restart_bot():
Перезапускает бота (сначала будет отправлено сообщение, возвращённое функцией `respond`)

#### set_startup_response(rsp):
Позволяет установить сообщение, которое будет отправлено сразу после выполнения
функции `restart_bot`

#### log(message, importance, t=time.time()):
Функция предназначена для отправки сообщений в панель логов на главном экране приложения.  
Принимает параметры `message` (str), `importance` (int) (от 0 до 3)

#### vkr
TODO