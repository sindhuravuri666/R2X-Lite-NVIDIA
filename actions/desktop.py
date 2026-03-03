import webbrowser
import urllib.parse
import datetime
import subprocess

def open_browser(url=None, query=None):
    if query:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    webbrowser.open(url)
    return f"Opened {url}"

def get_time():
    return str(datetime.datetime.now())

def open_notepad():
    subprocess.Popen("notepad")
    return "Opened Notepad"