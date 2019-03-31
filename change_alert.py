#!/usr/local/bin/python
import json
import time
from getpass import getpass
from urllib import request
import datetime
from mailServer import MailServer

target_url = "https://www.yesplanet.co.il//il/data-api-service/v1/quickbook/10100/films/until/{}?attr=&lang=he_IL"
total_films = []  # Total films that available
delay = 60 * 15   # Update rate
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
    settings = load_settings()  # Load saved settings
    if settings == -1:          # If there is no saved settings, load manually
        print("No settings file detected, please type your settings-")
        smtp = input("Please insert your smtp host:")
        port = input("Please insert the smtp's port:")
        username = input("Enter username:")
        password = getpass("Enter password:")
        target_mail = input("Enter a mail for updates:")
        # Save the settings
        save_settings(username, password, smtp, port, target_mail)
    else:
        smtp = settings[SMTP]
        port = settings[PORT]
        username = settings[USERNAME]
        password = settings[PASSWORD]
        target_mail = settings[DEST_MAIL]
    load_films()  # Load saved films
    try:
        # Setup smtp server
        srv = setup_server(username, password, smtp, port, target_mail)
        track_data(srv)  # Start loop for getting updates
    except Exception as e:
        print("!!Error!! - " + str(e))


def track_data(srv):
    """ This function is basically an infinite loop
        for getting the updates about the films
    """
    while True:
        data = get_data()  # Get the films
        updates = get_new_films(data)  # Find new films
        if len(updates) > 0:
            # Send a mail with the new films and add them to the list
            srv.sendMessage(compose_message(updates))
            total_films.extend(updates)
            save_films(data)  # Save the updates films into a file

        deleted = get_deleted_films(data)  # Get removed films
        if len(deleted) > 0:
            # Remove the the deleted films from the saved list
            log_delete(deleted)  # Log them to a file
            for film in deleted:
                total_films.remove(film)
            save_films(data)
        time.sleep(delay)


def get_new_films(data):
    """ Get the new films"""
    new_films = []
    for film in data:
        if film not in total_films:
            new_films.append(film)
    log(data, new_films)
    return new_films


def get_deleted_films(data):
    """ Get the deleted films """
    deleted_films = []
    if len(total_films) == 0:
        return None
    for film in total_films:
        if film not in data:
            deleted_films.append(film)
    return deleted_films


def log_delete(data):
    """ log to the console and to a file the deleted films """
    msg = "deleted - \n"
    for film in data:
        msg = msg + film + "\n"
    print(msg)
    msg_bytes = msg.encode(encoding="utf-8")
    try:
        f = open("script.log", "ab+")
        f.write(msg_bytes)
        f.close()
    except IOError as io_e:
        print("Error logging deleted file - " + str(io_e))
    except Exception as e:
        print("Unexpected Error - " + str(e))


def log(data1, data2):
    """ log to the console and to the file """
    t = datetime.datetime.now()
    msg = "{} | Total: {} | New: {}".format(t, len(data1), len(data2))
    print(msg.format(t, len(data1), len(data2)))
    try:
        f = open("script.log", "a+")
        f.write(msg + "\n")
        f.close()
    except IOError as io_e:
        print("An error had occurred: " + str(io_e))
    except Exception as e:
        print("An unexpected error had occurred: " + str(e))


def get_data():
    """ get the films from a request """
    # Parse the url with the current time to the API
    new_url = parse_url(target_url)
    res = request.urlopen(new_url)
    data = json.loads(res.read().decode())  # Get the JSON data
    films = data['body']['films']  # JSON list of films
    films_string = []
    for film in films:
        # JSON list to python list
        films_string.append(film['name'])
    return films_string


def setup_server(username, password, smtp, port, target_mail):
    """ setup a simple smtp server for sending the updates mail (very simple mail)"""
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
    """ load the smtp's server settings, return a list of the settings
        the format is USERNAME;PASSWORD;SMTP;PORT;DEST_ADDRESS
        **Not secured at all**
    """
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
    """ Load the saved films """
    try:
        # The films are saved in bytes (encoded UTF-8)
        f = open(films_file_name, "rb")
        for line in f:
            string_line = line.decode("utf-8")  # Decode as utf-8
            string_line = string_line.replace("\n", "")  # Remove the new lines
            # Add the saved films to the program
            total_films.append(string_line)
        f.close()
    except IOError:
        print("No past films were detected")
    except Exception as e:
        print("Unexpected error while saving the films - " + str(e))


def save_films(data):
    """ Save the total films after the current update """
    try:
        open(films_file_name, "w").close()
        # Write in bytes because Hebrew is problamatic
        f = open(films_file_name, "wb+")
        for line in data:
            # Encodes the string and save it to the file
            byte_string = (line + "\n").encode(encoding="utf-8")
            f.write(byte_string)
        f.close()
    except IOError:
        print("Could not save the films locally")
    except Exception as e:
        print("(UNEXPECTED! Could not save the films locally - " + str(e))


def save_settings(username, password, smtp, port, dest_addr):
    """Save settings with a format:
        USERNAME;PASSWORD;SMTP_SERVER;PORT;DEST_ADDR
        *** therefore the password could not include ';'
         - to fix it, the format should be with new lines
    """
    try:
        # Write to the file and parse it with ';' delimeters
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
    # Return an url with the correct time (based on the API)
    date = datetime.datetime.now()
    date = date.replace(year=date.year + 1)
    new_date = date.strftime("%Y-%m-%d")
    return url.format(date.strftime(new_date))


if __name__ == "__main__":
    main()
