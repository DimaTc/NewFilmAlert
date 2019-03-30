import json
import time
from getpass import getpass
from urllib import request
import datetime
from mailServer import MailServer

target_url = "https://www.yesplanet.co.il//il/data-api-service/v1/quickbook/10100/films/until/{}?attr=&lang=he_IL"
total_films = []
delay = 60 * 15
settings_file_name = "Settings.dat"
films_file_name = "films.dat"
USERNAME = 0
PASSWORD = 1
SMTP = 2
PORT = 3
DEST_MAIL = 4


def main():
    print("Setting up the server...")
    time.sleep(1.2)
    settings = load_settings()
    if settings == -1:
        print("No settings file detected, please type your settings-")
        smtp = input("Please insert your smtp host:")
        port = input("Please insert the smtp's port:")
        username = input("Enter username:")
        password = getpass("Enter password:")
        target_mail = input("Enter a mail for updates:")
        save_settings(username, password, smtp, port, target_mail)
    else:
        smtp = settings[SMTP]
        port = settings[PORT]
        username = settings[USERNAME]
        password = settings[PASSWORD]
        target_mail = settings[DEST_MAIL]
    load_films()
    try:
        srv = setup_server(username, password, smtp, port, target_mail)
        track_data(srv)
    except:
        print("!!Error!!")


def track_data(srv):
    while True:
        data = get_data()
        updates = get_new_films(data)
        if len(updates) > 0:
            srv.sendMessage(compose_message(updates))
            total_films.extend(updates)
            save_films(data)
        deleted = get_deleted_films(data)
        if len(deleted) > 0:
            print("Deleted films:")
            for film in deleted:
                total_films.remove(film)
                print("\t-" + film)
        time.sleep(delay)


def get_new_films(data):
    new_films = []
    for film in data:
        if film not in total_films:
            new_films.append(film)
    log(data, new_films)
    return new_films


def get_deleted_films(data):
    deleted_films = []
    if len(total_films) == 0:
        return None
    for film in total_films:
        if film not in data:
            deleted_films.append(film)
    return deleted_films


def log(data1, data2):
    t = datetime.datetime.now()
    msg = "{} | Total: {} | New: {}"
    print(msg.format(t, len(data1), len(data2)))


def get_data():
    new_url = parse_url(target_url)
    res = request.urlopen(new_url)
    data = json.loads(res.read().decode())
    films = data['body']['films']
    films_string = []
    for film in films:
        films_string.append(film['name'])
    return films_string


def setup_server(username, password, smtp, port, target_mail):
    mail_srv = MailServer(username, password, smtp, port)
    mail_srv.set_target(target_mail)
    return mail_srv


def compose_message(msg):
    msg_body = """\
        Film Updates


        {}
    """
    return msg_body.format(msg)


def load_settings():
    try:
        f = open(settings_file_name, "r")
        settings_string = f.read()
        f.close()
        return settings_string.split(';')
    except FileNotFoundError:
        print("File Not found!")
        return -1
    except IOError:
        print("IO error")
        return -1


def load_films():
    try:
        f = open(films_file_name, "rb")
        for line in f:
            string_line = line.decode("utf-8")
            string_line = string_line.replace("\n", "")
            total_films.append(string_line)
        f.close()
    except IOError:
        print("No past films were detected")
    except Exception as e:
        print("Unexpected error while saving the films - " + str(e))


def save_films(data):
    try:
        f = open(films_file_name, "wb+")
        for line in data:
            byte_string = line + "\n"
            f.write(byte_string.encode(encoding="utf-8"))
        f.close()
    except IOError:
        print("Could not save the films locally")
    except Exception as e:
        print("(UNEXPECTED! Could not save the films locally - " + str(e))


def save_settings(username, password, smtp, port, dest_addr):
    """For broader use, should be separated by a line not a semicolon"""
    try:
        f = open(settings_file_name, "w+")
        f.write(username + ";")
        f.write(password + ";")
        f.write(smtp + ";")
        f.write(port + ";")
        f.write(dest_addr)
        f.close()
        return 0
    except IOError:
        print("IO error")
        return -1
    except Exception as e:
        print("Unexpected Error!" + str(e))
        return -1


def parse_url(url):
    date = datetime.datetime.now()
    date = date.replace(year=date.year + 1)
    new_date = date.strftime("%Y-%m-%d")
    return url.format(date.strftime(new_date))


if __name__ == "__main__":
    main()
