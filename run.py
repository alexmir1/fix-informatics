########################################################################
#
# (C) 2017, Alexey Mironov <alexmir0x1@gmail.com>
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this code.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

import requests
from lxml import html
import time


def post_request(url, data=None, cookies=None, files=None, timeout=10):
    """
    post request with exception handling
    :param url: url to make request
    :param data: data to send
    :param cookies: cookies to send
    :param files: files to send
    :param timeout: close connect after timeout seconds
    :return: request object if request make without exceptions. Else None
    """
    try:
        return requests.post(url, data=data, cookies=cookies, files=files, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        pass
    except requests.exceptions.ReadTimeout:
        pass


def get_request(url, data=None, cookies=None, timeout=10):
    """
    get request with exception handling
    :param url: url to make request
    :param data: data to send
    :param cookies: cookies to send
    :param timeout: close connect after timeout seconds
    :return: request object if request make without exceptions. Else None
    """
    try:
        return requests.get(url, data=data, cookies=cookies, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        pass
    except requests.exceptions.ReadTimeout:
        pass


def get_page(url, data=None, cookies=None):
    """
    Load page until it loaded success
    :param url: page url
    :param data: data to request
    :param cookies: cookies to request
    :return: request object
    """
    r = get_request(url, data=data, cookies=cookies)
    while r is None or r.status_code == 500:
        time.sleep(1)
        r = get_request(url, data=data, cookies=cookies)
    return r


def auth(username, password):
    """
    Authenticates at informatics.msk.ru
    :param username: username at informatics
    :param password: password at informatics
    :return: (cookies with session key, user id at informatics)
    """
    url = 'http://informatics.msk.ru/login/index.php'
    r = post_request(url, dict(username=username, password=password), cookies={})
    while r is None or len(r.history) == 0:
        time.sleep(1)
        r = post_request(url, dict(username=username, password=password), cookies={})
    page = html.fromstring(r.text)
    id_data = page.xpath('//*[@id="footer"]/div/a')[0]
    user_id = id_data.attrib['href']\
        .replace('http://informatics.msk.ru/user/view.php?id=', '').replace('&course=1', '')
    return r.history[0].cookies, user_id


def get_problem_id(id, cookies=None):
    """
    get real problem id from id from link
    :param id: id from link
    :param cookies: auth with permissions to see with problem
    :return: real problem id
    """
    url = 'http://informatics.msk.ru/mod/statements/view3.php?id={}'.format(id)
    r = get_page(url, cookies=cookies)
    if r.status_code == 200:
        page = html.fromstring(r.text)
        return page.xpath('//*[@id="problem_id"]')[0].text
    elif r.status_code == 404:
        return id
    else:
        raise Exception()


class Run:
    """
    make run to submit at informatics.msk.ru
    """
    def __init__(self, problem_id, file_patch, lang_id, cookies, user_id):
        """
        :param problem_id: problem number
        :param file_patch: absolute or relative path
        :param lang_id: lang_id at informatics
        :param cookies: session auth cookies
        :param user_id: user id at informatics
        """
        self.problem_id = problem_id
        self.file = file_patch
        self.lang_id = lang_id
        self.cookies = cookies
        self.user_id = user_id
        self.submits = set()

    def get_submits(self):
        """
        get submits from informatics with curent problem, user id and lang
        :return: table from informatics
        """
        url = 'http://informatics.msk.ru/moodle/ajax/ajax.php?problem_id={}&from_timestamp=-1&to_timestamp=-1&group_id=0&user_id={}&lang_id={}&status_id=-1&statement_id=0&objectName=submits&count=500&with_comment=&page=0&action=getHTMLTable' \
            .format(self.problem_id, self.user_id, self.lang_id)
        r = get_page(url)
        text = r.json()['result']['text']
        page = html.fromstring(text)
        rows = page.xpath('//table')[0].findall('tr')
        data = list()
        for row in rows:
            data.append([c.text for c in row.getchildren()])
        return data

    def get_source(self, run):
        """
        get source code
        :param run: run id which source need
        :return: string with source code
        """
        contest_id, run_id = run.split('-')
        url = 'http://informatics.msk.ru/moodle/ajax/ajax_file.php?objectName=source&contest_id={}&run_id={}' \
            .format(contest_id, run_id)
        r = get_page(url, cookies=self.cookies)
        page = html.fromstring(r.text)
        data = page.xpath('//div/textarea')[0]
        return data.text

    def has_submitted(self):
        """
        Check has this source already submitted
        :return: run id if has. Else None
        """
        source = open(self.file).read()
        submits = self.get_submits()
        for submit in submits[1:]:
            submit_id = submit[0]
            if submit_id not in self.submits:
                if self.get_source(submit_id) == source:
                    return submit_id
                else:
                   self.submits.add(submit_id)

    def submit(self):
        """
        submit run to informatics
        :return: run id
        """
        url = 'http://informatics.msk.ru/py/problem/{}/submit'.format(self.problem_id)
        was_submitted = self.has_submitted()
        while was_submitted is None:
            time.sleep(1)
            r = post_request(url, data={'lang_id': self.lang_id}, cookies=self.cookies,
                             files=dict(file=open(self.file)), timeout=1)
            was_submitted = self.has_submitted()
        return was_submitted


if __name__ == '__main__':
    login = input('login: ')
    password = input('password: ')
    cookies, user_id = auth(login, password)
    print('auth success')
    problem_id = get_problem_id(input('problem number from title or id from url: '), cookies)
    print('ok. problem number: {}'.format(problem_id))
    file = input('file patch: ')
    lang_id = input("""Language                 id
    Free Pascal 2.6.2:        1
    GNU C 4.9                 2
    GNU C++ 4.9               3
    Borland Delphi 6 - 14.5   8
    Java JDK 1.7             18
    PHP 5.2.17               22
    Python 2.7               23
    Perl 5.10.1              24
    Mono C# 2.10.8.0         25
    Ruby 1.8.7               26
    Python 3.3               27
    Haskell GHC 7.4.2        28
    FreeBASIC 1.00.0         29
    PascalABC 1.8.0.496      30
    lang id: """)
    submit = Run(problem_id, file, lang_id, cookies, user_id).submit()
    print("Submitted, run_id: " + submit)
