# coding=utf-8
import requests
import time


def post_request(url, data=None, cookies=None, files=None, timeout=10):
    try:
        return requests.post(url, data=data, cookies=cookies, files=files, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        print('ConnectTimeout')
    except requests.exceptions.ReadTimeout:
        print('ReadTimeout')


def get_request(url, data=None, cookies=None, timeout=10):
    try:
        return requests.get(url, data=data, cookies=cookies, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        print('ConnectTimeout')
    except requests.exceptions.ReadTimeout:
        print('ReadTimeout')


def auth(username, password):
    url = 'http://informatics.msk.ru/login/index.php'
    r = post_request(url, dict(username=username, password=password), cookies={})
    while r is None or len(r.history) == 0:
        time.sleep(1)
        r = post_request(url, dict(username=username, password=password), cookies={})
    print('Auth success')
    return r.history[0].cookies


def get_page(url, data=None, cookies=None):
    r = get_request(url, data=data, cookies=cookies)
    while r is None:
        time.sleep(1)
        r = get_request(url, data=data, cookies=cookies)
    return r


def get_test_id(problem_id, cookies):
    try:
        page = get_page('http://informatics.msk.ru/mod/statements/view3.php?id={}'.format(problem_id), cookies=cookies).text
        j = page.index('/py/problem/') + len('/py/problem/')
        k = j
        while page[k].isdigit():
            k += 1
        return int(page[j:k])
    except:
        time.sleep(1)
        return get_test_id(problem_id, cookies)


def submit(file, problem_id, cookies):
    url = 'http://informatics.msk.ru/py/problem/{}/submit'.format(problem_id)
    while True:
        time.sleep(1)
        r = post_request(url, data={'lang_id': 3}, cookies=cookies, files=dict(file=open(file)), timeout=1)


submit('Source.cpp', 111134, auth('login', 'password'))
