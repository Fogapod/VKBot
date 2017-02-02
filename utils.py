# -*- coding: utf-8 -*-
import re
import time

class Profiler():
    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, type, value, traceback):
        print('Время выполнения: {:.3f} с.'.format(time.time() - self._startTime))


def parse_input(string, replace_vkurl=True, replace_url=True):
	new_string = string

	if replace_vkurl:
		new_string = re.sub(r'\b(https?://)?m\.?vk\.com/?.*\b',
			'__vkurl__',
			new_string # поиск ссылок vk.com
		)

	if replace_url:
		new_string = re.sub(
		r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/?)(?:[^\s()<>]+|(([^\s()<>]+|(([^\s()<>]+)))*))+(?:(([^\s()<>]+|(([^\s()<>]+)))*)|[^\s`!()[]{};:'".,<>?«»“”‘’]))'''
		, '__url__', # поиск всех остальных ссылок
		new_string
	)

	return new_string