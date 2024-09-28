import gspread
import json
import os
import pandas as pd

with open('config.json', 'r') as f:
    conf = json.load(f)

conf = {
  "type": "service_account",
  "project_id": "shaped-kite-420114",
  "private_key_id": os.environ.get('private_key_id'),
  "private_key": os.environ.get('private_key').replace('\\n', '\n'),
  "client_email": os.environ.get('client_email'),
  "client_id": os.environ.get('client_id'),
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/myaccauntchanels%40shaped-kite-420114.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

#Открываем таблицу
gc = gspread.service_account_from_dict(conf)
sh = gc.open("Опрос студентов о базовых кафедрах бакалавриата (Отзывы)")
worksheet = sh.sheet1

#Достаем значения
list_of_lists = worksheet.get_all_values()

info_str = '''
# Полезные ссылки

* Записи презентаций 2021 года на [youtube](https://youtube.com/playlist?list=PLdLtk23ZM3V7HPXdvZj4dEYntgMFOwIr2)
* Записи презентаций 2020 года на [youtube](https://www.youtube.com/playlist?list=PLdLtk23ZM3V5iepbbpiyHRNGK9GS2YP-E). 
* Хорошая (2020) [**статья**](https://vk.com/@miptfpmi-kafedry-fpmi?anchor=kafedry-fpmi-nauka-fupm-matematicheskaya-fizika) про кафедры.
* [Гитхаб](https://github.com/s0mth1ng/DepartmentsOfFPMI) с ответами 2019-2020 годов
* Сама [**форма**](https://forms.gle/tRwK6HTUhvdqAssB7). 

Если Вы уже учитесь или когда-то учились на базовой кафедре бакалавриата ФПМИ и Вам есть чем поделиться, пожалуйста, заполните.

Ответы автоматически подтягиваются с формы.

'''

def lstrip_to_letter(s):
    s = ' '.join([i for i in s.split() if len(i) > 0])
    for i in range(len(s)):
        if s[i].isalnum():
            return s[i:]
    return s

def get_answers(df, title):
    tmp_str = f'\n{title}\n'
    found = False
    for c in df.columns[1:]:
        answers = []
        for ind, ans in enumerate(df[c]):
            if ans is None or len(ans) <= 1:
                continue
            answers.append(f'**({df.iloc[ind, 0]})** {lstrip_to_letter(ans)}')
        if answers:
            found = True
            tmp_str += f'\n### {c}\n'
            tmp_str += '\n'.join([f'{ind + 1}. {ans}' for ind,
                                 ans in enumerate(answers)])
    if found:
        return tmp_str
    return ''

df = pd.DataFrame(list_of_lists[1:], columns=list_of_lists[0])
for i in range(3, 8):
    df[df.columns[i]] = pd.to_numeric(df[df.columns[i]])

departments = sorted(list(set(df.iloc[:, 1])))

if len(departments) > 0:
    info_str += '# Содержание:\n'
    for i, depart in enumerate(departments):
        info_str += f'{i}) [{depart}](#{"-".join((depart.lower().replace(".", "").replace(")", "").replace("(", "")).replace('"', "")).split())})\n'

for depart in departments:
    d_info = df.loc[df[df.columns[1]] == depart]
    d_numbers = d_info.iloc[:, 3:8].mean().round(2)
    d_numbers = pd.DataFrame(
        {'Вопрос': [
                'Личные впечатления',
                'Соответствие ожиданиям',
                'Соотношение полезных, по Вашему мнению, предметов',
                'Среднее качество работы преподавателей',
                '"Халявность" кафедры'
            ],
         'Оценка (среднее по 10-бальной шкале)': d_numbers.values
        }
    )
    info_str += f'\n# {depart}\n'
    info_str += f'\n## Количество ответов: {(df[df.columns[1]] == depart).sum()}.\n'
    info_str += f'\n## Оценки от студентов и выпускников.\n'
    info_str += f'\n{d_numbers.to_markdown(index=False)}\n'
    info_str += get_answers(d_info.iloc[:, [2]+list(range(8, 18))], '## Общие вопросы.')
    info_str += get_answers(d_info.iloc[:, [2]+list(range(18, 23))], '## Про науку.')
    info_str += get_answers(d_info.iloc[:, [2]+list(range(23, 25))], '## Индустрия.')
    info_str += get_answers(d_info.iloc[:, [2]+list(range(25, 27))], '## Другое.')

with open('README.md', 'w') as f:
    f.write(info_str + '\n')
