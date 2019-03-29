import json
import threading
import time
from getpass import getpass
from urllib import request
import datetime
from mailServer import MailServer

target_url = "https://www.yesplanet.co.il//il/data-api-service/v1/quickbook/10100/films/until/{}?attr=&lang=he_IL"
global mail_srv
total_films = []
delay = 60 * 15


def main():
    print("Setting up the server...")
    time.sleep(1.2)
    smtp = input("Please insert your smtp host:")
    port = input("Please insert the smtp's port:")
    username = input("Enter username:")
    password = getpass("Enter password:")
    target_mail = input("Enter a mail for updates:")
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
            srv.sendMessage(composeMessage(updates))
            total_films.extend(data)
        time.sleep(delay)


def get_new_films(data):
    new_films = []
    for film in data:
        if film not in total_films:
            new_films.append(film)
    log(data, new_films)
    return new_films


def log(data1, data2):
    t = datetime.datetime.now()
    msg = "{} | Total: {} | New: {}"
    print(msg.format(t, len(data1), len(data2)))


def get_data():
    new_url = parseUrl(target_url)
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


def composeMessage(msg):
    msg_body = """\
        Subject: Updates
        Updates


        {}
    """
    return msg_body.format(msg)


def parseUrl(url):
    date = datetime.datetime.now()
    date = date.replace(year=date.year + 1)
    new_date = date.strftime("%Y-%m-%d")
    return target_url.format(date.strftime(new_date))


if __name__ == "__main__":
    main()
