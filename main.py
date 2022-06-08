import requests
from urllib.parse import quote
import urllib.request
from re import finditer, MULTILINE
from time import sleep
import PySimpleGUI as sg
from PIL import Image, ImageTk
from io import BytesIO
import os
from pathlib import Path
from tkinter import Tk
tk = Tk()
tk.withdraw()

with open("settings.cfg", "r", encoding="utf-8", errors="ignore") as settings:
    working_url = settings.read()
try:
    response_code = requests.get(working_url, timeout=2).status_code
    if response_code != 200:
        raise TimeoutError
except:
    try:
        i = int(working_url.split('https://a')[1].split('.agorov.org/')[0])
    except:
        i = 0
    while True:
        working_url = f"https://a{i}.agorov.org/"
        try:
            response_code = requests.get(working_url, timeout=2).status_code
            if response_code == 200:
                break
        except:
            pass
        i+=1
with open("settings.cfg", "w", encoding="utf-8", errors="ignore") as settings:
    settings.write(working_url)

def do_search_request(default_url, search_string):
    anime_name = []
    anime_url = []
    anime_description = []
    anime_image = []
    search_url = f"{default_url}index.php?do=search&subaction=search&search_start=0&full_search=0&result_from=1&story={quote(search_string)}"
    http_content = requests.get(search_url).content.decode("utf-8", errors="ignore")
    total_pages = http_content.count('<a onclick="javascript:list_submit') + 2
    for i in range(1, total_pages):
        search_url = f"{default_url}index.php?do=search&subaction=search&search_start={i}&full_search=0&result_from=1&story={quote(search_string)}"
        while True:
            try:
                http_content = requests.get(search_url, timeout=2).content.decode("utf-8", errors="ignore")
                sleep(1)
                break
            except:
                sleep(2)
        regex = r"(?:<h2>\s*<a href=\")([^\"]+)(?:\"\>)([^\/]+)(?:[^\[]+)(\[[^\]]+\])"
        matches = finditer(regex, http_content, MULTILINE)
        for _, match in enumerate(matches, start=1):   
            anime_url.append(match.group(1))
            anime_name.append(f"{match.group(2)}{match.group(3)}")
        regex = r"(?:<p><strong>Описание:\s</strong>)([^\<]+)"
        matches = finditer(regex, http_content, MULTILINE)
        for _, match in enumerate(matches, start=1):   
            anime_description.append(match.group(1))
        regex = r"(?:<img class=\"imgRadius\" src=\"/)([^\"]+)"
        matches = finditer(regex, http_content, MULTILINE)
        for _, match in enumerate(matches, start=1):   
            anime_image.append(f"{default_url}{match.group(1)}")
        window['-BAR-'].update_bar(i*(10000/(total_pages-1)))
    return anime_url, anime_name, anime_description, anime_image

default_img = Image.open(BytesIO(requests.get("https://i.ibb.co/3FLbJBL/default-image.png").content))

left_side =     [
                [sg.Listbox(key='-LIST-', size=(40, 30), values=[])]
                ]

right_side =    [
                [sg.Text(size=(5, 1)), sg.Image(key='-IMAGE-', size=(40, 8))], 
                [sg.Text(size=(5, 1)), sg.Multiline(key='-DESCRIPTION-'+sg.WRITE_ONLY_KEY, size=(40,6))]
                ]

layout =    [
            [sg.Input(key='-INPUT-', size=(96, 1), right_click_menu=['&Edit', ['Заменить на содержимое буфера обмена',]]), sg.Button(key='-SEARCH-', button_text="Поиск", bind_return_key=True)],
            [sg.Column(left_side, element_justification='c'), sg.VSeperator(),sg.Column(right_side, element_justification='c')],
            [sg.ProgressBar(10000, orientation='h', key="-BAR-", size=(67, 20))],
            [sg.Button(key='-EXIT-', button_text='Выйти'), sg.Text(key='-STATUS-', justification='center', text='Ожидание...', size=(76, 1)), sg.Button(key='-DOWNLOAD-', button_text='Скачать')]
            ]

window = sg.Window('Загрузчик Аниме', layout, finalize=True, icon='icon.ico')

while True:
    event, values = window.read(timeout=16)
    if event in (sg.WIN_CLOSED, '-EXIT-'):
        break
    if event == 'Заменить на содержимое буфера обмена':
        window['-INPUT-'].update(tk.clipboard_get())
    if (event == "-SEARCH-") and (len(values['-INPUT-'])!=0):
        window['-STATUS-'].update('Поиск аниме...')
        window['-BAR-'].update_bar(0)
        anime_url, anime_name, anime_description, anime_image = do_search_request(working_url, values['-INPUT-'])
        window['-BAR-'].update_bar(10000)
        window['-STATUS-'].update('Ожидание...')
        window['-LIST-'].update(anime_name)
    if len(values['-LIST-'])!=0:
        if selected_anime!=values['-LIST-'][0]:
            window['-STATUS-'].update('Загрузка информации об аниме...')
            selected_anime=values['-LIST-'][0]
            img = Image.open(BytesIO(requests.get(anime_image[anime_name.index(selected_anime)]).content))
            window['-IMAGE-'].update(data=ImageTk.PhotoImage(img))
            window['-DESCRIPTION-'+sg.WRITE_ONLY_KEY].update(anime_description[anime_name.index(selected_anime)])
            window['-STATUS-'].update('Ожидание...')
    else:
        window['-IMAGE-'].update(data=ImageTk.PhotoImage(default_img))
        selected_anime = ''
    if event == '-DOWNLOAD-':
        window['-STATUS-'].update('Ожидание указания пути...')
        window['-BAR-'].update_bar(0)
        location = sg.popup_get_folder('Куда будем сохранять аниме?') + '/'
        window['-STATUS-'].update('Анализ выходной папки...')
        os.chdir(location)
        try:
            os.mkdir(selected_anime.split(' [')[0].replace(':', ';'))
        except:
            pass
        location += selected_anime.split(' [')[0].replace(':', ';') + '/'
        files = []
        for r, d, f in os.walk(location):
            for _file in f:
                if '.mp4' in _file:
                    files.append(os.path.join(r, _file))
        window['-STATUS-'].update('Поиск ссылок для скачивания...')
        http_content = requests.get(anime_url[anime_name.index(selected_anime)]).content.decode(encoding='utf-8', errors='ignore')
        data = http_content.split('var data = {"')[1].split(',};')[0].split('","')
        epizode_name = []
        epizode_id = []
        for line in data:
            line = line.split('":"')
            epizode_name.append(line[0].replace('"', ''))
            epizode_id.append(line[1].replace('"', ''))
        for i in range(len(epizode_id)):
            window['-STATUS-'].update(f"Скачивается {epizode_name[i]}...")
            http_content = requests.get(f"https://play.animegost.org/{epizode_id[i]}?old=1").content.decode(encoding='utf-8', errors='ignore')
            download_links = []
            regex = r"(?:href=\")([^\"]+)"
            matches = finditer(regex, http_content, MULTILINE)
            for _, match in enumerate(matches, start=1):   
                download_links.append(match.group(1))
            if (location + epizode_name[i] + '.mp4') in files:
                epizode_size = int(Path(location + epizode_name[i] + '.mp4').stat().st_size)
                for e in range(len(download_links)-1, -1, -1):
                    try:
                        response = requests.head(download_links[e])
                        if int(response.headers["Content-Length"])*0.8 >= epizode_size:
                            urllib.request.urlretrieve(download_links[e], filename=f"{location}{epizode_name[i]}.mp4")
                            window['-BAR-'].update_bar(i*(10000/(len(epizode_id)-1)))
                        else:
                            window['-BAR-'].update_bar((i+1)*(10000/(len(epizode_id)-1)))
                        break
                    except IOError:
                        pass
            else:
                for e in range(len(download_links)-1, -1, -1):
                    try:
                        urllib.request.urlretrieve(download_links[e], filename=f"{location}{epizode_name[i]}.mp4")
                        window['-BAR-'].update_bar((i+1)*(10000/(len(epizode_id)-1)))
                        break
                    except IOError:
                        continue
        sg.popup('Загрузка завершена!', f"Аниме {selected_anime.split(' [')[0]} успешно скачано!")
        window['-STATUS-'].update('Ожидание...')
window.close()
