#coding:utf8


import random
import re


class Plugin(object):
    __doc__ = '''Плагин предназначен для использования пользовательских команд.
    Использование: -
    Пример: -'''

    name = 'custom_command'
    keywords = (name)
    priority = 500
    protection = 0
    argument_required = False

    rsp = None

    def _accept_request(self, msg, rsp, utils, *args, **kwargs):
        custom_commands = utils.get_custom_commands()

        if not custom_commands:
            return False

        response = ''

        for key in random.sample(custom_commands.keys(),
                                len(custom_commands.keys())):

            if custom_commands[key][0][1] == 2:  # use regex
                pattern = re.compile(key, re.U + re.I)
                if pattern.search(msg.text):
                    for resp in random.sample(
                                              custom_commands[key],
                                              len(custom_commands[key])):
                        if resp[5] == 2:  # disabled
                            continue
                        else:
                            choice = resp
                            response = choice[0]

                    if response:
                        groups = pattern.findall(msg.text)
                        groupdict = pattern.search(msg.text).groupdict()
                        response = \
                            utils.safe_format(response, *groups, **groupdict)
                        break

            elif msg.text.lower() == key:
                for resp in random.sample(custom_commands[key],
                                          len(custom_commands[key])):
                    if resp[5] == 2:  # disabled
                        continue
                    else:
                        choice = resp
                        response = choice[0]

                if response:
                    break

        if not response:
            return False

        if choice[4] == 1:  # works only WITHOUT appeal
            if msg.was_appeal:
                return False

        elif choice[4] == 2:  # works only WITH appeal
            if not msg.was_appeal:
                return False

        if choice[3] == 2:  # force forward
            rsp.forward_msg = msg.msg_id

        elif choice[3] == 1:  # never forward
            rsp.forward_msg = 0

        if choice[2] == 2:  # do not mark message
            rsp.do_mark = False

        if response.startswith('self='):
            msg.text = '_' + response[5:]

            return self._accept_request(msg, rsp, utils, *args, **kwargs)


        self.rsp = rsp
        self.rsp.text = response

        return True

    def respond(self, *args, **kwargs):
        return self.rsp