import requests
from tqdm import tqdm
import sys
import time
import urllib.request
import urllib.parse
import urllib
import re
from tkinter import filedialog as fd
import os
from pathlib import Path


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path, description):
    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=description) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)


def askfolder():
    _file_name = fd.askdirectory(title='Выберите папку для сохранения всех аниме...')
    _settings = open('settings.conf', 'w')
    _settings.write(_file_name)
    _settings.close()
    return _file_name


def get_from_link(_link):
    try:
        _response = requests.get(_link)
        return _response
    except IOError:
        try:
            _response = requests.get(_link)
            return _response
        except IOError:
            try:
                _response = requests.get(_link)
                return _response
            except IOError:
                print(
                    'Не удалось получить информацию с сайта animevost.org...\nВероятно ваш IP был заблокирован...')
                time.sleep(0.01)
                for _ in tqdm(range(10), desc='Завершение программы'):
                    time.sleep(1)
                sys.exit(0)


root = fd.Tk()
root.withdraw()


try:
    settings = open('settings.conf', 'r')
    for line in settings:
        current_string = str(line)
        break
    settings.close()
    file_name = current_string
except FileNotFoundError:
    file_name = askfolder()
except NameError:
    file_name = askfolder()

anime_name = []
anime_link = []
files = []

vklink = 'https://vk.com/animevostorg'
response = requests.get(vklink)
html_content = response.content.decode('utf8')
main_link = html_content.split('https://')[2][:html_content.split('https://')[2].find('/')]

print('Введите название аниме:', end=' ')
name = str(input())

link = 'https://' + main_link + '/index.php?do=search&subaction=search&search_start=0&full_search=0&result_from=1&story=' + urllib.parse.quote(
    name)
response = get_from_link(link)

regex = '<a onclick=\"javascript:list_submit'
matches = re.finditer(regex, str(response.content.decode('utf8')), re.MULTILINE)
for matchNum, match in enumerate(matches, start=1):
    search_pages = matchNum
try:
    search_pages += 1
except NameError:
    search_pages = 1

regex = r"(?:\t\t<div class=\"shortstory\">\s+<div class=\"shortstoryHead\">\s+<h2>\s+<a href=\")(.+)(?:<\/a>\s+<\/h2>\s+<\/div>\s+<div class=\"staticInfo\">)"

for e in tqdm(range(1, search_pages + 1), desc='Сканируем страницы с аниме'):
    link = 'https://' + main_link + '/index.php?do=search&subaction=search&search_start=' + str(
        e) + '&full_search=0&result_from=1&story=' + urllib.parse.quote(name)
    response = get_from_link(link)
    matches = re.finditer(regex, str(response.content.decode('utf8')), re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):
        info = str(match.group()).split('<a href="')[1]
        info = info.split('</a>')[0]
        anime_name.append(info.split('">')[1])
        anime_link.append(info.split('">')[0] + '\n')
i = 0
while True:
    try:
        print(str(i + 1) + ') ' + anime_name[i])
        i += 1
    except IndexError:
        if i == 0:
            i = -1
        break
if i == -1:
    print('Такое Аниме не найдено!')
    time.sleep(0.01)
    for _ in tqdm(range(10), desc='Завершение программы'):
        time.sleep(1)
    sys.exit(0)


print('Выберите аниме из списка:', end=' ')
anime_num = int(input())

os.chdir(file_name + '/')
try:
    os.mkdir(anime_name[anime_num - 1][:anime_name[anime_num - 1].find(' / ')].replace(':', ';'))
except FileExistsError:
    pass
file_name += '/' + anime_name[anime_num - 1][:anime_name[anime_num - 1].find(' / ')].replace(':', ';') + '/'
for r, d, f in os.walk(file_name):
    for file in f:
        if '.mp4' in file:
            files.append(os.path.join(r, file))
response = get_from_link(anime_link[anime_num - 1])
html_content = response.content.decode('utf8')
data = html_content[
       html_content.find('var data = {"') + 13:html_content.find('"}', html_content.find('var data = {"') + 13)]
data_list = data.split('","')
epizode_name = []
epizode_code = []
for i in range(len(data_list)):
    try:
        epizode_name.append(data_list[i].split('":"')[0])
        epizode_code.append(data_list[i].split('":"')[1])
    except IndexError:
        break
for i in range(len(epizode_code)):
    link = 'https://play.animegost.org/' + epizode_code[i] + '?player=9'
    response = get_from_link(link)
    html_content = response.content.decode('utf8')
    data = html_content[html_content.find('"file":"') + 8:html_content.find('",', html_content.find('"file":"') + 8)]
    data_list = data.split(',')
    download_link = []
    for e in range(len(data_list)):
        download_link.append(data_list[e][data_list[e].find(']')+1:data_list[e].find(' ', data_list[e].find(']')+1)])
    if (file_name + epizode_name[i] + '.mp4') in files:
        epizode_size = int(Path(file_name + epizode_name[i] + '.mp4').stat().st_size)
        e = len(download_link) - 1
        while e >= 0:
            try:
                response = requests.head(download_link[e])
                if int((int(response.headers["Content-Length"]))*0.8) >= epizode_size:
                    download_url(download_link[e], file_name + epizode_name[i] + '.mp4', epizode_name[i])
                else:
                    print(epizode_name[i], 'уже была скачана!')
                break
            except IOError:
                e -= 1
    else:
        e = len(download_link) - 1
        while e >= 0:
            try:
                download_url(download_link[e], file_name + epizode_name[i] + '.mp4', epizode_name[i])
                break
            except IOError:
                e -= 1
print('Все серии были скачаны!')
