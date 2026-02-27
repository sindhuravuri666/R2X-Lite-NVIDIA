import webbrowser
import datetime
import subprocess

def open_browser(url):
    webbrowser.open(url)
    return f"Opened {url}"

def get_time():
    return str(datetime.datetime.now())

def open_notepad():
    subprocess.Popen("notepad")
    return "Opened Notepad"