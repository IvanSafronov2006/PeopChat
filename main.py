#Подключение библиотек
from flask import Flask, render_template, url_for, request, redirect
from datetime import datetime, date
import sqlite3
import datetime
import random

app = Flask(__name__)


#Окно регистрации
@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == "POST":
        # Получаем данные из формы ввода
        p = request.form.to_dict()
        name = p['name']
        surname = p['surname']
        login = p['email']
        password = p['password']
        f = 'photo.png'
        photo = 'static/img/' + str(f)
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        result = basa.execute("""SELECT * FROM people WHERE login = (?)""",
                              (login,)).fetchall()
        e = ''

        # Проверка на логин
        if len(result) >= 1:
            e += 'Данный логин уже зарегистрирован.'
        elif len(login) < 8:
            e += 'Длина вашего логина должна быть больше 8 символов.'
        elif len(password) < 8:
            e += 'Длина вашего пароля должна быть больше 8 символов.'
        if e != '':
            return render_template('registration.html', error=e)
        else:
            # Запись в БД
            basa.execute('INSERT INTO People (surname, name, login, password, photo) VALUES (?, ?, ?, ?, ?)',
                         (name,
                          surname,
                          login,
                          password,
                          photo))
            basa_d.commit()
            result = basa.execute("""SELECT * FROM people WHERE login = (?)""", (login,)).fetchall()
            basa.execute('INSERT INTO PeopleCommunities (id_people, id_community, status) VALUES (?, ?, ?)',
                         (result[0][0],
                          1,
                          0))
            basa_d.commit()
            file = open('user_id.txt', 'w')
            file.write(str(result[0][0]))
            file.close()
            file_2 = open('entries.txt', 'w')
            file_2.write('0')
            file_2.close()
            return redirect('load_photo')
    else:
        name = ''
        surname = ''
        login = ''
        password = ''
        photo = ''
        e = ''
        return render_template('registration.html', error=e)


#Окно входа
@app.route('/', methods=['POST', 'GET'])
@app.route('/gateway', methods=['POST', 'GET'])
def gateway():
    if request.method == "POST":
        # Получение данных из формы ввода
        p = request.form.to_dict()
        login = p['email']
        password = p['password']
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        result = basa.execute("""SELECT * FROM people WHERE login = (?)""",
                              (login,)).fetchall()
        e = ''

        # Проверка на логин и пароль
        if len(result) < 1:
            e = 'Данный логин не зарегистрирован.'
            return render_template('gateway.html',
                                   login=login,
                                   password=password,
                                   error=e)
        else:
            if result[0][4] != password:
                e = 'Ваш пароль неверен.'
                return render_template('gateway.html',
                                       login=login,
                                       password=password,
                                       error=e)
        if e == '':
            result = basa.execute("""SELECT * FROM people WHERE login = (?)""",
                                  (login,)).fetchall()
            file = open('user_id.txt', 'w')
            file.write(str(result[0][0]))
            file.close()
            file_2 = open('entries.txt', 'w')
            file_2.write('0')
            file_2.close()
            print('True')
            return redirect('main_menu')
    else:
        login = ''
        password = ''
        e = ''
        return render_template('gateway.html', login=login, password=password, error=e)


#Главная страница
#Отображение новостей, последних событий
@app.route('/main_menu', methods=['POST', 'GET'])
def main_menu():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                              (id_people,)).fetchall()
        photo = result[0][5]
        name = result[0][1] + ' ' + result[0][2]

        # Получаем список друзей
        result = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                              (id_people,)).fetchall()
        spis_friend = []
        for i in result:
            if i[0] == id_people:
                spis_friend.append(i[1])
            else:
                spis_friend.append(i[0])

        # Получаем список подписок
        spis_com = []
        result = basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?)""",
                              (id_people,)).fetchall()
        for i in result:
            spis_com.append(i[1])

        # Получаем список записей людей
        spis_entries_people = []
        for people in spis_friend:
            result = basa.execute("""SELECT * FROM PeopleEntries WHERE id_people = (?)""",
                                  (people,)).fetchall()
            for entry in result:
                res = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (entry[0],)).fetchall()
                a = ['other_profile/' + str(people),
                     res[0][5],
                     res[0][1] + ' ' + res[0][2],
                     entry[1],
                     entry[2],
                     entry[3]]
                spis_entries_people.append(a)

        # Получаем список записей сообществ
        spis_entries_com = []
        for com in spis_com:
            result = basa.execute("""SELECT * FROM CommunityEntries WHERE id_community = (?)""", (com,)).fetchall()
            for entry in result:
                res = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""", (entry[0],)).fetchall())
                a = ['community/' + str(entry[0]),
                     res[0][3],
                     res[0][1],
                     entry[1],
                     entry[2],
                     entry[3]]
                spis_entries_com.append(a)

        # Соединение всех записей, их сортировка и выбор последних 10
        spis_all_entries = spis_entries_com + spis_entries_people
        spis_all_entries.sort(key=lambda x: -1 * int(x[-1]))
        entry_number = int(str(list(open('entries.txt'))[0]).strip())
        otvet = spis_all_entries[entry_number:entry_number + 10]
        file = open('entries.txt', 'w')
        if entry_number >= len(spis_all_entries):
            file.write('0')
        else:
            file.write(str(entry_number + 10))
        file.close()

        return render_template('main_menu.html',
                               photo=photo,
                               name=name,
                               entries=otvet)
    elif request.method == 'POST':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                              (id_people,)).fetchall()
        photo = result[0][5]
        name = result[0][1] + ' ' + result[0][2]

        # Получаем список друзей
        result = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                              (id_people,)).fetchall()
        spis_friend = []
        for i in result:
            if i[0] == id_people:
                spis_friend.append(i[1])
            else:
                spis_friend.append(i[0])

        # Получаем список подписок
        spis_com = []
        result = basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?)""",
                              (id_people,)).fetchall()
        for i in result:
            spis_com.append(i[1])

        # Получаем список записей людей
        spis_entries_people = []
        for people in spis_friend:
            result = basa.execute("""SELECT * FROM PeopleEntries WHERE id_people = (?)""",
                                  (people,)).fetchall()
            for entry in result:
                res = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (entry[0],)).fetchall()
                a = ['other_profile/' + str(people),
                     res[0][5],
                     res[0][1] + ' ' + res[0][2],
                     entry[1],
                     entry[2],
                     entry[3]]
                spis_entries_people.append(a)

        # Получаем список записей сообществ
        spis_entries_com = []
        for com in spis_com:
            result = basa.execute("""SELECT * FROM CommunityEntries WHERE id_community = (?)""",
                                  (com,)).fetchall()
            for entry in result:
                res = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                        (entry[0],)).fetchall())
                a = ['community/' + str(entry[0]),
                     res[0][3],
                     res[0][1],
                     entry[1],
                     entry[2],
                     entry[3]]
                spis_entries_com.append(a)

        # Соединение всех записей, их сортировка и выбор последних 10
        spis_all_entries = spis_entries_com + spis_entries_people
        spis_all_entries.sort(key=lambda x: -1 * int(x[-1]))
        entry_number = int(str(list(open('entries.txt'))[0]).strip())
        otvet = spis_all_entries[entry_number:entry_number + 10]
        file = open('entries.txt', 'w')
        if entry_number >= len(spis_all_entries):
            file.write('0')
        else:
            file.write(str(entry_number + 10))
        file.close()
        return render_template('main_menu.html',
                               photo=photo,
                               name=name,
                               entries=otvet)


#Профиль пользователя
@app.route('/my_profile')
def my_profile():
    # Подключение к БД
    basa_d = sqlite3.connect("mess.db")
    basa = basa_d.cursor()
    id_people = int(str(list(open('user_id.txt'))[0]))
    result = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                          (id_people,)).fetchall()
    photo = result[0][5]
    name = result[0][1] + ' ' + result[0][2]
    res = basa.execute("""SELECT * FROM PeopleEntries WHERE id_people = (?)""",
                       (id_people,)).fetchall()
    otvet = []
    for entry in res:
        a = [photo, name, entry[1], entry[2], entry[3]]
        otvet.append(a)
    return render_template('my_profile.html',
                           photo=photo,
                           name=name,
                           entries=otvet[::-1])


#Список групп и друзей пользователя
@app.route('/messages', methods=['POST', 'GET'])
def messages():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))

        # Получаем список сообщений
        result = list(basa.execute("""SELECT * FROM PeopleChat WHERE id_1 = (?) OR id_2 = (?)""",
                                   (id_people,
                                    id_people)).fetchall())
        result.sort(key=lambda x: int(x[-1]))

        # Исключаем все повторяющиеся id
        peoples = []
        for i in result:
            if (i[0] not in peoples) and i[0] != id_people:
                peoples.append(i[0])
            elif (i[1] not in peoples) and i[1] != id_people:
                peoples.append(i[1])
        otvet = []
        for id_p in peoples:
            res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (id_p,)).fetchall())[0]
            people = ['message/' + str(res[0]) + '/0',
                      res[1] + ' ' + res[2],
                      res[5]]
            otvet.append(people)

        # Получаем информацию о чатах в группах
        groups = []
        result_g = list(basa.execute("""SELECT * FROM PeopleGroup WHERE id_peop = (?)""",
                                     (id_people,)).fetchall())
        for i in result_g:
            groups.append(i[1])
        otvet_2 = []
        for i in groups:
            res = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                    (i,)).fetchall())[0]
            gr = ['g_message/' + str(res[0]) + '/0',
                  res[1],
                  res[3]]
            otvet_2.append(gr)

        # Получаем информацию пользователе
        result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (id_people,)).fetchall())[0]
        name = result[1] + ' ' + result[2]
        photo = result[-1]
        return render_template('messages.html',
                               photo=photo,
                               name=name,
                               messages=otvet,
                               messages_2=otvet_2)
    else:
        return redirect('add_chat')


#Загрузка фото профиля
@app.route('/load_photo', methods=['POST', 'GET'])
def load_photo():
    file = url_for('static',
                   filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фотографии</h1>
                            <h3 align="center">для вашей регистрации</h3>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Получаем фото
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png', 'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}', 'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')

        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_p = int(list(open('user_id.txt'))[0].strip())
        basa.execute("""UPDATE People SET photo = (?) WHERE id = (?)""",
                     (file, id_p))
        basa_d.commit()
        return redirect('main_menu')


#Загрузка фото группы
@app.route('/load_photo_2', methods=['POST', 'GET'])
def load_photo_2():
    file = url_for('static',
                   filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка вашей фотографии</h1>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Получаем фото
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png', 'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}', 'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')

        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_p = int(list(open('user_id.txt'))[0].strip())
        basa.execute("""UPDATE People SET photo = (?) WHERE id = (?)""",
                     (file, id_p))
        basa_d.commit()
        return redirect('my_profile')


#Чат с другим пользователем
@app.route('/message/<int:id_pep>/<int:number>', methods=['POST', 'GET'])
def peoples_messages(id_pep, number):
    if request.method == 'GET':
        file = open('now_mess.txt', 'w')
        file.write('0')
        file.close()

        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (id_people,)).fetchall())[0]
        name = result[1] + ' ' + result[2]
        photo = result[5]
        ssulk = '/other_profile/' + str(id_pep)
        result_2 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                     (id_pep,)).fetchall())[0]
        name_2 = result_2[1] + ' ' + result_2[2]
        photo_2 = result_2[5]

        messages = list(basa.execute(
            """SELECT * FROM PeopleChat WHERE ((id_1 = (?)) AND (id_2 = (?))) OR ((id_1 = (?)) AND (id_2 = (?)))""",
            (id_people, id_pep, id_pep, id_people)).fetchall())
        messages.sort(key=lambda x: int(x[-1]), reverse=True)
        file = int(list(open('now_mess.txt'))[0])
        messages = messages[file * 10:(file + 1) * 10]
        mess = []

        for i in range(min(len(messages), 10)):
            a = []
            if messages[i][0] == id_people:
                a.append(1)
            else:
                a.append(2)
            res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (messages[i][0],)).fetchall())[0]
            a.append(res[5])
            a.append(res[1] + ' ' + res[2])
            a.append(messages[i][2])
            mess.append(a)
        return render_template('chat.html',
                               photo=photo,
                               name=name,
                               ssulk=ssulk,
                               photo_2=photo_2,
                               name_2=name_2,
                               mess=mess[::-1])
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        p = request.form.to_dict()
        if p['value'] == 'up':
            number = int(list(open('now_mess.txt'))[0]) + 1
            file = open('now_mess.txt', 'w')
            file.write(str(number))
            file.close()

            # Подключение к БД
            basa_d = sqlite3.connect("mess.db")
            basa = basa_d.cursor()
            id_people = int(str(list(open('user_id.txt'))[0]))
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            name = result[1] + ' ' + result[2]
            photo = result[5]
            ssulk = '/other_profile/' + str(id_pep)
            result_2 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                         (id_pep,)).fetchall())[0]
            name_2 = result_2[1] + ' ' + result_2[2]
            photo_2 = result_2[5]

            messages = list(basa.execute(
                """SELECT * FROM PeopleChat WHERE ((id_1 = (?)) AND (id_2 = (?))) OR ((id_1 = (?)) AND (id_2 = (?)))""",
                (id_people, id_pep, id_pep, id_people)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            file = int(list(open('now_mess.txt'))[0])
            messages = messages[file * 10:(file + 1) * 10]

            if len(messages) == 0:
                file = open('now_mess.txt', 'w')
                file.write('0')
                file.close()

            mess = []
            for i in range(min(len(messages), 10)):
                a = []
                if messages[i][0] == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                        (messages[i][0],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   ssulk=ssulk,
                                   photo_2=photo_2,
                                   name_2=name_2,
                                   mess=mess[::-1])

        elif p['value'] == 'down':
            number = int(list(open('now_mess.txt'))[0]) - 1
            file = open('now_mess.txt', 'w')
            if number < 0:
                file.write('0')
            else:
                file.write(str(number))
            file.close()

            # Подключение к БД
            basa_d = sqlite3.connect("mess.db")
            basa = basa_d.cursor()
            id_people = int(str(list(open('user_id.txt'))[0]))
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            name = result[1] + ' ' + result[2]
            photo = result[5]
            ssulk = '/other_profile/' + str(id_pep)
            result_2 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                         (id_pep,)).fetchall())[0]
            name_2 = result_2[1] + ' ' + result_2[2]
            photo_2 = result_2[5]
            messages = list(basa.execute(
                """SELECT * FROM PeopleChat WHERE ((id_1 = (?)) AND (id_2 = (?))) OR ((id_1 = (?)) AND (id_2 = (?)))""",
                (id_people, id_pep, id_pep, id_people)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            file = int(list(open('now_mess.txt'))[0])
            messages = messages[file * 10:(file + 1) * 10]

            mess = []
            for i in range(min(len(messages), 10)):
                a = []
                if messages[i][0] == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""", (messages[i][0],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   ssulk=ssulk,
                                   photo_2=photo_2,
                                   name_2=name_2,
                                   mess=mess[::-1])
        else:
            basa_d = sqlite3.connect("mess.db")
            basa = basa_d.cursor()
            tt = int(list(open('time.txt'))[0]) + 1
            id_people = int(str(list(open('user_id.txt'))[0]))
            basa.execute('INSERT INTO PeopleChat (id_1, id_2, text, time) VALUES (?, ?, ?, ?)',
                         (id_people, id_pep, str(p['message']).strip(), tt))
            basa_d.commit()
            file = open('time.txt', 'w')
            file.write(str(tt))
            file.close()
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            name = result[1] + ' ' + result[2]
            photo = result[5]
            ssulk = '/other_profile/' + str(id_pep)
            result_2 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                         (id_pep,)).fetchall())[0]
            name_2 = result_2[1] + ' ' + result_2[2]
            photo_2 = result_2[5]
            messages = list(basa.execute(
                """SELECT * FROM PeopleChat WHERE ((id_1 = (?)) AND (id_2 = (?))) OR ((id_1 = (?)) AND (id_2 = (?)))""",
                (id_people, id_pep, id_pep, id_people)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            mess = []
            messages = messages[:10]
            for i in range(min(len(messages), 10)):
                a = []
                if messages[i][0] == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                        (messages[i][0],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   photo_2=photo_2,
                                   ssulk=ssulk,
                                   name_2=name_2,
                                   mess=mess[::-1])


#Просмотр сообщества
@app.route('/community/<int:id_comm>', methods=['POST', 'GET'])
def community(id_comm):
    if request.method == 'GET':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (id_people,)).fetchall())[0]
        result_2 = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                     (id_comm,)).fetchall())[0]
        name = result[1] + ' ' + result[2]
        photo = result[5]
        name_2 = result_2[1]
        photo_2 = result_2[3]
        entries = []
        res = list(basa.execute("""SELECT * FROM CommunityEntries WHERE id_community = (?)""",
                                (id_comm,)).fetchall())
        for i in res:
            a = [photo_2, str(name_2), str(i[1]), i[2]]
            entries.append(a)
        entries = entries[::-1]

        # Выяснием подписанность человека
        phrase = ''
        pod = list(basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?) AND id_community = (?)""",
                                (id_people, id_comm)).fetchall())
        status = pod[0][-1]
        if len(pod) == 0:
            phrase = 'Подписаться'
        else:
            if pod[0][2] == 1:
                phrase = 'Удалить сообщество'
            else:
                phrase = 'Отписаться'
        r = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                              (id_comm,)).fetchall())
        text = r[0][2]
        return render_template('community.html',
                               photo=photo,
                               ssulk=str('/add_com_entries/' + str(id_comm)),
                               status=status,
                               phrase=phrase,
                               name=name,
                               photo_2=photo_2,
                               name_2=name_2,
                               text=text,
                               entries=entries)
    elif request.method == 'POST':
        p = request.form.to_dict()
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (id_people,)).fetchall())[0]
        result_2 = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                     (id_comm,)).fetchall())[0]
        name = result[1] + ' ' + result[2]
        photo = result[5]
        name_2 = result_2[1]
        photo_2 = result_2[3]
        entries = []
        res = list(basa.execute("""SELECT * FROM CommunityEntries WHERE id_community = (?)""",
                                (id_comm,)).fetchall())
        for i in res:
            a = [photo_2,
                 str(name_2),
                 str(i[1]),
                 i[2]]
            entries.append(a)
        entries = entries[::-1]

        # Выяснием подписанность человека
        phrase = ''
        pod = list(basa.execute("""SELECT * FROM PeopleCommunities WHERE (id_people = (?)) AND (id_community = (?))""",
                                (id_people, id_comm)).fetchall())
        status = pod[0][-1]
        if len(pod) == 0:
            basa.execute('INSERT INTO PeopleCommunities (id_people, id_community, status) VALUES (?, ?, ?)',
                         (id_people, id_comm, 0))
            basa_d.commit()
            phrase = 'Отписаться'
        else:
            if pod[0][2] == 0:
                basa.execute('DELETE FROM PeopleCommunities WHERE (id_people = (?)) AND (id_community = (?))',
                             (id_people, id_comm))
                basa_d.commit()
                phrase = 'Подписаться'
            else:
                basa.execute('DELETE FROM PeopleCommunities WHERE (id_community = (?))',
                             (id_comm,))
                basa_d.commit()
                basa.execute('DELETE FROM Communities WHERE (id = (?))',
                             (id_comm,))
                basa_d.commit()
                basa.execute('DELETE FROM CommunityEntries WHERE (id_community = (?))',
                             (id_comm,))
                basa_d.commit()
                return redirect('/main_menu')
        r = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                              (id_comm,)).fetchall())
        text = r[2]
        return render_template('community.html',
                               photo=photo,
                               status=status,
                               ssulk=str('/add_com_entries/' + str(id_comm)),
                               phrase=phrase,
                               name=name,
                               photo_2=photo_2,
                               name_2=name_2,
                               text=text,
                               entries=entries)


#Просмотр профиля другого человека
@app.route('/other_profile/<int:id_peop>', methods=['GET', 'POST'])
def other_profile(id_peop):
    if request.method == 'GET':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result0 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (id_people,)).fetchall())[0]
        result = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                              (id_peop,)).fetchall()
        photo = result0[5]
        name = result0[1] + ' ' + result0[2]
        photo2 = result[0][5]
        name2 = result[0][1] + ' ' + result[0][2]
        res = basa.execute("""SELECT * FROM PeopleEntries WHERE id_people = (?)""",
                           (id_peop,)).fetchall()
        otvet = []
        for entry in res:
            a = [photo2,
                 name2,
                 entry[1],
                 entry[2]]
            otvet.append(a)
        r = basa.execute("""SELECT * FROM Friends WHERE (id_p1 = (?)) AND (id_p2 = (?))""",
                         (id_people, id_peop)).fetchall()
        if len(r) == 0:
            phrase = 'Добавить в друзья'
        else:
            phrase = 'Удалить из друзей'
        return render_template('other_profile.html',
                               name=name,
                               phrase=phrase,
                               photo=photo,
                               photo_2=photo2,
                               name_2=name2,
                               entries=otvet[::-1])
    elif request.method == 'POST':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        ress = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                            (id_people,)).fetchall()
        check = True
        for i in ress:
            if i[1] == id_peop and check:
                check = False
                ress2 = basa.execute("""DELETE FROM Friends WHERE (id_p1 = (?)) AND (id_p2 = (?))""",
                                     (id_people, id_peop))
                basa_d.commit()
        if check:
            ress2 = basa.execute(f"""INSERT INTO Friends(id_p1, id_p2) VALUES({id_people}, {id_peop})""")
            basa_d.commit()

        result0 = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (id_people,)).fetchall())
        result = basa.execute("""SELECT * FROM People WHERE id = (?)""",
                              (id_peop,)).fetchall()
        photo = result0[0][5]
        name = str(result0[0][1]) + ' ' + str(result[0][2])
        photo2 = result[0][5]
        name2 = result[0][1] + ' ' + result[0][2]
        res = basa.execute("""SELECT * FROM PeopleEntries WHERE id_people = (?)""",
                           (id_peop,)).fetchall()
        otvet = []
        for entry in res:
            a = [photo2, name2, entry[1], entry[2]]
            otvet.append(a)
        r = basa.execute("""SELECT * FROM Friends WHERE (id_p1 = (?)) AND (id_p2 = (?))""",
                         (id_people, id_peop)).fetchall()
        if len(r) == 0:
            phrase = 'Добавить в друзья'
        else:
            phrase = 'Удалить из друзей'
        basa_d.commit()
        basa.close()
        return render_template('other_profile.html',
                               name=name,
                               phrase=phrase,
                               photo=photo,
                               photo_2=photo2,
                               name_2=name2,
                               entries=otvet[::-1])


#Информация обо всех группах, чатах и сообществах пользователя (подписки)
@app.route('/info', methods=['POST', 'GET'])
def info():
    if request.method == 'GET':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        friends_t = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                                 (id_people,)).fetchall()
        communy_t = basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?)""",
                                 (id_people,)).fetchall()
        groups__t = basa.execute("""SELECT * FROM PeopleGroup WHERE id_peop = (?)""",
                                 (id_people,)).fetchall()
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        friends = []
        communities = []
        groups = []

        # Добавляем информацию о друзьях
        for i in friends_t:
            people = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (i[1],)).fetchall())[0]
            a = []
            a.append('other_profile/' + str(people[0]))
            a.append(people[1] + ' ' + people[2])
            a.append(people[5])
            friends.append(a)

        # Добавляем информацию о группах
        for i in groups__t:
            group = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                      (i[1],)).fetchall())[0]
            a = []
            a.append('group/' + str(group[0]))
            a.append(group[1])
            a.append(group[3])
            groups.append(a)

        # Добавляем информацию о сообществах
        for i in communy_t:
            comm = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                     (i[1],)).fetchall())[0]
            a = []
            a.append('community/' + str(comm[0]))
            a.append(comm[1])
            a.append(comm[3])
            communities.append(a[:])
        return render_template('info.html',
                               name=name,
                               photo=photo,
                               entries_1=friends,
                               entries_2=groups,
                               entries_3=communities)
    else:
        p = request.form.to_dict()
        if p['value'] == 'communities':
            add_community()
        elif p['value'] == 'groups':
            add_group()
        else:
            basa_d = sqlite3.connect("mess.db")
            basa = basa_d.cursor()
            id_people = int(str(list(open('user_id.txt'))[0]))
            friends_t = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                                     (id_people,)).fetchall()
            communy_t = basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?)""",
                                     (id_people,)).fetchall()
            groups__t = basa.execute("""SELECT * FROM PeopleGroup WHERE id_peop = (?)""",
                                     (id_people,)).fetchall()
            inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (id_people,)).fetchall())[0]
            name = inf[1] + ' ' + inf[2]
            photo = inf[5]
            friends = []
            communities = []
            groups = []

            # Добавляем информацию о друзьях
            for i in friends_t:
                people = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                           (i[1],)).fetchall())[0]
                a = []
                a.append('other_profile/' + str(people[0]))
                a.append(people[1] + ' ' + people[2])
                a.append(people[5])
                friends.append(a)

            # Добавляем информацию о группах
            for i in groups__t:
                group = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                          (i[1],)).fetchall())[0]
                a = []
                a.append('group/' + str(group[0]))
                a.append(group[1])
                a.append(group[3])
                groups.append(a)

            # Добавляем информацию о сообществах
            for i in communy_t:
                comm = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                         (i[1],)).fetchall())[0]
                a = []
                a.append('community/' + str(comm[0]))
                a.append(comm[1])
                a.append(comm[3])
                communities.append(a[:])
            return render_template('info.html',
                                   name=name,
                                   photo=photo,
                                   entries_1=friends,
                                   entries_2=groups,
                                   entries_3=communities)


#Просмотр группы
@app.route('/group/<int:id_group>', methods=['POST', 'GET'])
def group(id_group):
    if request.method == 'GET':
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        result = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                   (id_group,)).fetchall())[0]
        name_2 = result[1]
        photo_2 = result[3]
        res = list(basa.execute("""SELECT * FROM PeopleGroup WHERE (id_group = (?)) AND (id_peop = (?))""",
                                (id_group,
                                 id_people)).fetchall())
        if len(res) != 0:
            if res[0][2] == 0:
                status = 0
            else:
                status = 1
        else:
            return redirect('/error')
        peops = list(basa.execute("""SELECT * FROM PeopleGroup WHERE id_group = (?)""",
                                  (id_group,)).fetchall())
        peoples = []
        ssulk = '/add_people/' + str(id_group)
        ssulk_2 = '/delete/' + str(id_group)
        for i in peops:
            peop = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                     (i[0],)).fetchall())[0]
            a = []
            a.append('other_profile/' + str(i[0]))
            a.append(peop[1] + ' ' + peop[2])
            a.append(peop[5])
            a.append(str(i[0]))
            peoples.append(a)
        return render_template('group.html',
                               name=name,
                               ssulk=ssulk,
                               ssulk_2=ssulk_2,
                               photo=photo,
                               name_2=name_2,
                               photo_2=photo_2,
                               status=status,
                               peoples=peoples)
    else:
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        p = request.form.to_dict()
        id_peop = int(p['value'])
        basa.execute('DELETE FROM PeopleGroup WHERE (id_peop = (?)) AND (id_group = (?))',
                     (id_peop,
                      id_group))
        basa_d.commit()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        result = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                   (id_group,)).fetchall())[0]
        name_2 = result[1]
        photo_2 = result[3]
        res = list(basa.execute("""SELECT * FROM PeopleGroup WHERE (id_group = (?)) AND (id_peop = (?))""",
                                (id_group,
                                 id_people)).fetchall())[0]
        if res[2] == 0:
            status = 0
        elif res[2] == 1:
            status = 1
        else:
            error()
        peops = list(basa.execute("""SELECT * FROM PeopleGroup WHERE id_group = (?)""",
                                  (id_group,)).fetchall())
        peoples = []
        for i in peops:
            peop = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                     (i[0],)).fetchall())[0]
            a = []
            a.append('other_profile/' + str(i[0]))
            a.append(peop[1] + ' ' + peop[2])
            a.append(peop[5])
            a.append(str(i[0]))
            peoples.append(a)
        try:
            return render_template('group.html',
                                   name=name,
                                   ssulk=ssulk,
                                   ssulk_2=ssulk_2,
                                   photo=photo,
                                   name_2=name_2,
                                   photo_2=photo_2,
                                   status=status,
                                   peoples=peoples)
        except Exception as E:
            print("Возникла ошибка в отображении группы >>>", E)
            return render_template('group.html',
                                   name=name,
                                   ssulk="ssulk",
                                   ssulk_2="ssulk_2",
                                   photo=photo,
                                   name_2=name_2,
                                   photo_2=photo_2,
                                   status=status,
                                   peoples=peoples)


#Удаление группы
@app.route('/delete/<int:id_g>')
def delete(id_g):
    # Подключение к БД
    basa_d = sqlite3.connect("mess.db")
    basa = basa_d.cursor()
    basa.execute('DELETE FROM Groups WHERE id = (?)',
                 (id_g,))
    basa.execute('DELETE FROM PeopleGroup WHERE id_group = (?)',
                 (id_g,))
    basa.execute('DELETE FROM GroupChat WHERE id_group = (?)',
                 (id_g,))
    basa_d.commit()

    if True:
        # Сохранение в БД
        id_people = int(str(list(open('user_id.txt'))[0]))
        friends_t = basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                                 (id_people,)).fetchall()
        communy_t = basa.execute("""SELECT * FROM PeopleCommunities WHERE id_people = (?)""",
                                 (id_people,)).fetchall()
        groups__t = basa.execute("""SELECT * FROM PeopleGroup WHERE id_peop = (?)""",
                                 (id_people,)).fetchall()
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        friends = []
        communities = []
        groups = []

        # Добавляем информацию о друзьях
        for i in friends_t:
            people = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (i[1],)).fetchall())[0]
            a = []
            a.append('other_profile/' + str(people[0]))
            a.append(people[1] + ' ' + people[2])
            a.append(people[5])
            friends.append(a)

        # Добавляем информацию о группах
        for i in groups__t:
            group = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                      (i[1],)).fetchall())[0]
            a = []
            a.append('group/' + str(group[0]))
            a.append(group[1])
            a.append(group[3])
            groups.append(a)

        # Добавляем информацию о сообществах
        for i in communy_t:
            comm = list(basa.execute("""SELECT * FROM Communities WHERE id = (?)""",
                                     (i[1],)).fetchall())[0]
            a = []
            a.append('community/' + str(comm[0]))
            a.append(comm[1])
            a.append(comm[3])
            communities.append(a[:])
        return render_template('info.html',
                               name=name,
                               photo=photo,
                               entries_1=friends,
                               entries_2=groups,
                               entries_3=communities)


#Вывод непредвиденных ошибок
@app.route('/error', methods=['POST', 'GET'])
def error():
    # Подключение к БД
    basa_d = sqlite3.connect("mess.db")
    basa = basa_d.cursor()
    id_people = int(str(list(open('user_id.txt'))[0]))
    inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                            (id_people,)).fetchall())[0]
    name = inf[1] + ' ' + inf[2]
    photo = inf[5]
    return render_template('error.html',
                           name=name,
                           photo=photo)


#Общение в группе
@app.route('/g_message/<int:id_gr>/<int:number>', methods=['POST', 'GET'])
def groups_messages(id_gr, number):
    if request.method == 'GET':
        file = open('now_mess.txt', 'w')
        file.write('0')
        file.close()

        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                   (id_people,)).fetchall())[0]
        name = result[1] + ' ' + result[2]
        photo = result[5]
        result_2 = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                     (id_gr,)).fetchall())[0]
        ssulk = '/group/' + str(id_gr)
        name_2 = result_2[1]
        photo_2 = result_2[3]

        messages = list(basa.execute("""SELECT * FROM GroupChat WHERE id_group = (?)""",
                                     (id_gr,)).fetchall())
        messages.sort(key=lambda x: int(x[-1]), reverse=True)
        file = int(list(open('now_mess.txt'))[0])
        messages = messages[file * 10:(file + 1) * 10]

        mess = []
        for i in range(min(len(messages), 10)):
            a = []
            if int(messages[i][1]) == id_people:
                a.append(1)
            else:
                a.append(2)
            res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (messages[i][1],)).fetchall())[0]
            a.append(res[5])
            a.append(res[1] + ' ' + res[2])
            a.append(messages[i][2])
            mess.append(a)
        return render_template('chat.html',
                               photo=photo,
                               ssulk=ssulk,
                               name=name,
                               photo_2=photo_2,
                               name_2=name_2,
                               mess=mess[::-1])
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        p = request.form.to_dict()

        if p['value'] == 'up':
            number = int(list(open('now_mess.txt'))[0]) + 1
            file = open('now_mess.txt', 'w')
            file.write(str(number))
            file.close()
            # Загрузка в БД
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            ssulk = '/group/' + str(id_gr)
            name = result[1] + ' ' + result[2]
            photo = result[5]
            result_2 = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                         (id_gr,)).fetchall())[0]
            name_2 = result_2[1]
            photo_2 = result_2[3]
            messages = list(basa.execute("""SELECT * FROM GroupChat WHERE id_group = (?)""",
                                         (id_gr,)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            file = int(list(open('now_mess.txt'))[0])
            messages = messages[file * 10:(file + 1) * 10]

            if len(messages) == 0:
                file = open('now_mess.txt', 'w')
                file.write('0')
                file.close()
            mess = []

            for i in range(min(len(messages), 10)):
                a = []
                if int(messages[i][1]) == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                        (messages[i][1],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   photo_2=photo_2,
                                   name_2=name_2,
                                   mess=mess[::-1])
        elif p['value'] == 'down':
            number = int(list(open('now_mess.txt'))[0]) - 1
            file = open('now_mess.txt', 'w')
            if number < 0:
                file.write('0')
            else:
                file.write(str(number))
            file.close()
            # Получаем из БД
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            ssulk = '/group/' + str(id_gr)
            name = result[1] + ' ' + result[2]
            photo = result[5]
            result_2 = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                         (id_gr,)).fetchall())[0]
            name_2 = result_2[1]
            photo_2 = result_2[3]
            messages = list(basa.execute("""SELECT * FROM GroupChat WHERE id_group = (?)""",
                                         (id_gr,)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            file = int(list(open('now_mess.txt'))[0])
            messages = messages[file * 10:(file + 1) * 10]

            mess = []
            for i in range(min(len(messages), 10)):
                a = []
                if int(messages[i][1]) == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                        (messages[i][1],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   photo_2=photo_2,
                                   name_2=name_2,
                                   mess=mess[::-1])
        else:
            # Подключение к БД
            basa_d = sqlite3.connect("mess.db")
            basa = basa_d.cursor()
            tt = int(list(open('time.txt'))[0]) + 1
            id_people = int(str(list(open('user_id.txt'))[0]))
            basa.execute('INSERT INTO GroupChat (id_group, id_people, text, time) VALUES (?, ?, ?, ?)',
                         (id_gr,
                          id_people,
                          str(p['message']).strip(),
                          tt))
            basa_d.commit()
            file = open('time.txt', 'w')
            file.write(str(tt))
            file.close()
            result = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                       (id_people,)).fetchall())[0]
            ssulk = '/group/' + str(id_gr)
            name = result[1] + ' ' + result[2]
            photo = result[5]
            result_2 = list(basa.execute("""SELECT * FROM Groups WHERE id = (?)""",
                                         (id_gr,)).fetchall())[0]
            name_2 = result_2[1]
            photo_2 = result_2[3]
            messages = list(basa.execute("""SELECT * FROM GroupChat WHERE id_group = (?)""",
                                         (id_gr,)).fetchall())
            messages.sort(key=lambda x: int(x[-1]), reverse=True)
            file = int(list(open('now_mess.txt'))[0])
            messages = messages[file * 10:(file + 1) * 10]

            mess = []
            for i in range(min(len(messages), 10)):
                a = []
                if int(messages[i][1]) == id_people:
                    a.append(1)
                else:
                    a.append(2)
                res = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                        (messages[i][1],)).fetchall())[0]
                a.append(res[5])
                a.append(res[1] + ' ' + res[2])
                a.append(messages[i][2])
                mess.append(a)
            return render_template('chat.html',
                                   photo=photo,
                                   name=name,
                                   photo_2=photo_2,
                                   name_2=name_2,
                                   mess=mess[::-1])


#Поиск групп, людей и сообществ
@app.route('/finder', methods=['POST', 'GET'])
def finder():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('finder.html',
                               name=name,
                               photo=photo,
                               entries_1=[],
                               entries_2=[])
    elif request.method == 'POST':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        p = request.form.to_dict()
        inquiry = p['find'].lower()
        print(inquiry)
        peoples = list(basa.execute("""SELECT * FROM People""").fetchall())
        community = list(basa.execute("""SELECT * FROM Communities""").fetchall())
        entries_1 = []
        entries_2 = []

        for i in peoples:
            n = str(i[1] + i[2]).lower()
            print(n)
            if str(inquiry) in str(n.lower()):
                answer = [f'other_profile/{i[0]}',
                          i[1] + ' ' + i[2],
                          i[5]]
                entries_1.append(answer)

        for i in community:
            n = str(i[1]).lower()
            if str(inquiry) in str(n.lower()):
                answer = [f'community/{i[0]}',
                          i[1],
                          i[3]]
                entries_2.append(answer)
        print(entries_1)
        return render_template('finder.html',
                               name=name,
                               photo=photo,
                               entries_1=entries_1,
                               entries_2=entries_2)


#Изменение профиля
@app.route('/edit_profile', methods=['POST', 'GET'])
def edit_profile():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('edit_profile.html',
                               name=name,
                               photo=photo)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        p = request.form.to_dict()

        # Обновление БД
        name = p['name']
        surname = p['surname']
        basa.execute("""UPDATE People SET surname = (?) WHERE id = (?)""",
                     (surname,
                      id_people))
        basa_d.commit()
        basa.execute("""UPDATE People SET name = (?) WHERE id = (?)""",
                     (name,
                      id_people))
        basa_d.commit()
        return redirect('/main_menu')


#Создание сообщества
@app.route('/add_community', methods=['POST', 'GET'])
def add_community():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('add_1.html',
                               name=name,
                               photo=photo)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        p = request.form.to_dict()
        # Запись в БД
        name = p['name']
        text = p['text']
        basa.execute('INSERT INTO Communities (name, text, photo) VALUES (?, ?, ?)',
                     (name,
                      text,
                      'statis/img/photo.png'))
        basa_d.commit()
        comm = list(basa.execute("""SELECT * FROM Communities""").fetchall())[-1]
        basa.execute('INSERT INTO PeopleCommunities (id_people, id_community, status) VALUES (?, ?, ?)',
                     (id_people,
                      comm[0],
                      1))
        basa_d.commit()
        return redirect('load_photo_3/' + str(comm[0]))


#Создание группы
@app.route('/add_group', methods=['POST', 'GET'])
def add_group():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('add_2.html',
                               name=name,
                               photo=photo)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        p = request.form.to_dict()
        # Запись в БД
        name = p['name']
        text = p['text']
        basa.execute('INSERT INTO Groups (name, text, photo) VALUES (?, ?, ?)',
                     (name,
                      text,
                      'static/img/photo.png'))
        basa_d.commit()
        gr = list(basa.execute("""SELECT * FROM Groups""").fetchall())[-1]
        basa.execute('INSERT INTO PeopleGroup (id_peop, id_group, status) VALUES (?, ?, ?)',
                     (id_people, gr[0], 1))
        basa_d.commit()
        return redirect('load_photo_4/' + str(gr[0]))


#Изменение фото сообщества
@app.route('/load_photo_3/<int:id_c>', methods=['POST', 'GET'])
def load_photo_3(id_c):
    file = url_for('static', filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фото сообщества</h1>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Сохранение фото на сервер
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        basa.execute("""UPDATE Communities SET photo = (?) WHERE id = (?)""",
                     (file, id_c))
        basa_d.commit()
        return redirect('/community/' + str(id_c))


#Изменение фото группы
@app.route('/load_photo_4/<int:id_g>', methods=['POST', 'GET'])
def load_photo_4(id_g):
    file = url_for('static',
                   filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фото группы</h1>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Сохранение фото на сервер
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        basa.execute("""UPDATE Groups SET photo = (?) WHERE id = (?)""",
                     (file,
                      id_g))
        basa_d.commit()
        return redirect('/add_people/' + str(id_g))


#Добавление в друзья/удаление из друзей
@app.route('/add_people/<int:id_g>', methods=['POST', 'GET'])
def add_people(id_g):
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        peoples = list(basa.execute("""SELECT * FROM Friends WHERE (id_p1 = (?))""",
                                    (id_people,)).fetchall())
        otvet = []
        for i in peoples:
            people = list(basa.execute("""SELECT * FROM People WHERE (id = (?))""",
                                       (i[1],)).fetchall())[0]
            p = list(basa.execute("""SELECT * FROM PeopleGroup WHERE (id_peop = (?)) AND (id_group = (?))""",
                                  (i[1], id_g)).fetchall())
            a = []
            a.append(people[1] + ' ' + people[2])
            a.append(people[5])
            a.append(str(people[0]))
            if len(p) == 0:
                a.append('Добавить')
            else:
                a.append('Удалить')
            otvet.append(a)
        return render_template('add_in_group.html',
                               name=name,
                               photo=photo,
                               otvet=otvet)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        p = request.form.to_dict()
        id_add = int(p['value'])
        if id_add != 0:
            res = list(basa.execute("""SELECT * FROM PeopleGroup WHERE (id_peop = (?)) AND (id_group = (?))""",
                                    (id_add,
                                     id_g)).fetchall())
            if len(res) == 0:
                basa.execute('INSERT INTO PeopleGroup (id_peop, id_group, status) VALUES (?, ?, ?)',
                             (id_add, id_g, 0))
                basa_d.commit()
            else:
                basa.execute('DELETE FROM PeopleGroup WHERE (id_peop = (?)) AND (id_group = (?))',
                             (id_add, id_g))
                basa_d.commit()
            id_people = int(str(list(open('user_id.txt'))[0]))
            inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                    (id_people,)).fetchall())[0]
            name = inf[1] + ' ' + inf[2]
            photo = inf[5]
            peoples = list(basa.execute("""SELECT * FROM Friends WHERE (id_p1 = (?))""",
                                        (id_people,)).fetchall())
            otvet = []

            for i in peoples:
                people = list(basa.execute("""SELECT * FROM People WHERE (id = (?))""",
                                           (i[1],)).fetchall())[0]
                a = []
                a.append(people[1] + ' ' + people[2])
                a.append(people[5])
                a.append(str(people[0]))
                p = list(basa.execute("""SELECT * FROM PeopleGroup WHERE (id_peop = (?)) AND (id_group = (?))""",
                                      (i[1],
                                       id_g)).fetchall())
                print(len(p))
                if len(p) == 0:
                    a.append('Добавить')
                else:
                    a.append('Удалить')
                otvet.append(a)
            basa_d.close()
            return render_template('add_in_group.html',
                                   name=name,
                                   photo=photo,
                                   otvet=otvet)
        else:
            return redirect('/group/' + str(id_g))


#Добавление собственной записи
@app.route('/add_my_entries', methods=['POST', 'GET'])
def add_my_entries():
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('add_my_entries.html',
                               name=name,
                               photo=photo)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]

        p = request.form.to_dict()
        text = p['text']
        time = int(list(open('time.txt'))[0]) + 1
        file = open('time.txt',
                    'w')
        file.write(str(time))
        file.close()

        basa.execute('INSERT INTO PeopleEntries (id_people, text, photo, time) VALUES (?, ?, ?, ?)',
                     (id_people,
                      text,
                      'static/img/photo.png',
                      time))
        basa_d.commit()

        return redirect('load_photo_5/' + str(time))


#Загрузка фото для записи
@app.route('/load_photo_5/<int:time>', methods=['POST', 'GET'])
def load_photo_5(time):
    file = url_for('static',
                   filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фото для записи</h1>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Сохранение фото на сервер
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        basa.execute("""UPDATE PeopleEntries SET photo = (?) WHERE time = (?)""",
                     (file,
                      time))
        basa_d.commit()
        return redirect('/my_profile')


#Создание записи в сообществе
@app.route('/add_com_entries/<int:id_g>', methods=['POST', 'GET'])
def add_com_entries(id_g):
    if request.method == 'GET':
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]
        return render_template('add_com_entries.html',
                               name=name,
                               photo=photo)
    else:
        # Подключение к БД
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        id_people = int(str(list(open('user_id.txt'))[0]))
        inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                                (id_people,)).fetchall())[0]
        name = inf[1] + ' ' + inf[2]
        photo = inf[5]

        p = request.form.to_dict()
        text = p['text']
        time = int(list(open('time.txt'))[0]) + 1
        file = open('time.txt',
                    'w')
        file.write(str(time))
        file.close()

        basa.execute('INSERT INTO CommunityEntries (id_community, text, photo, time) VALUES (?, ?, ?, ?)',
                     (id_g,
                      text,
                      'static/img/photo.png',
                      time))
        basa_d.commit()

        return redirect('/load_photo_6/' + str(time))


#Изменение фото записи сообщества
@app.route('/load_photo_6/<int:time>', methods=['POST', 'GET'])
def load_photo_6(time):
    file = url_for('static',
                   filename='img/photo.png')
    if request.method == 'GET':
        # Загрузка фото
        return f'''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
                            <link rel="stylesheet" type="text/css" href="{url_for('static', filename='css/style.css')}" />
                            <title>Выбор фото</title>
                          </head>
                          <body>
                            <h1 align="center">Загрузка фото для записи сообщества</h1>
                            <div>
                                <form class="login_form" method="post" enctype="multipart/form-data">
                                   <div class="form-group">
                                        <label for="photo">Приложите фотографию</label>
                                        <input type="file" class="form-control-file" id="photo" name="file">
                                    </div>
                                    <img src="{file}" width="200" height="200" alt="Фото">
                                    <br>
                                    <button type="submit" class="btn btn-primary">Отправить</button>
                                </form>
                            </div>
                          </body>
                        </html>'''
    elif request.method == 'POST':
        # Сохранение фото на сервер
        f = request.files['file']
        if str(f.filename) == '':
            with open(f'photo.png',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/photo.png')
        else:
            with open(f'static/img/{f.filename}',
                      'wb') as file:
                file.write(f.read())
            file = url_for('static',
                           filename=f'img/{f.filename}')
        basa_d = sqlite3.connect("mess.db")
        basa = basa_d.cursor()
        basa.execute("""UPDATE CommunityEntries SET photo = (?) WHERE time = (?)""",
                     (file, time))
        basa_d.commit()
        id_g = list(basa.execute("""SELECT * FROM CommunityEntries WHERE time = (?)""",
                                 (time,)).fetchall())[0][0]
        return redirect('/community/' + str(id_g))


#Создание чата с другим пользователем
@app.route('/add_chat')
def add_chat():
    # Подключение к БД
    basa_d = sqlite3.connect("mess.db")
    basa = basa_d.cursor()
    id_people = int(str(list(open('user_id.txt'))[0]))
    inf = list(basa.execute("""SELECT * FROM People WHERE id = (?)""",
                            (id_people,)).fetchall())[0]
    name = inf[1] + ' ' + inf[2]
    photo = inf[5]
    inf_t = list(basa.execute("""SELECT * FROM Friends WHERE id_p1 = (?)""",
                              (id_people,)).fetchall())
    inf = []
    for i in inf_t:
        inf.append(i[1])
    inf2 = list(basa.execute("""SELECT * FROM People""").fetchall())
    peoples = []
    for i in inf2:
        if i[0] in inf:
            peoples.append([i[5], i[1] + ' ' + i[2], '/message/' + str(i[0]) + '/0'])
    return render_template('add_chat.html',
                           name=name,
                           photo=photo,
                           peoples=peoples)


#Запуск
if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
