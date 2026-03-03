import webbrowser
import urllib.parse
import datetime
import subprocess

def open_browser(url=None, query=None):
    if query:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        webbrowser.open(url)
        return f"Opening YouTube for {query}"

    if url:
        webbrowser.open(url)
        return "Opening browser"

def get_time():
    return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"

def open_notepad():
    subprocess.Popen("notepad")
    return "Opening Notepad"