# addon.py
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import sys, json, urllib.request, urllib.parse
import resolveurl
import os

EXPECTED_ID = "plugin.video.easyflix"
ADDON = xbmcaddon.Addon()
ACTUAL_ID = ADDON.getAddonInfo("id")
if ACTUAL_ID != EXPECTED_ID:
    xbmcgui.Dialog().ok("Error", "Addon ID Mismatch!")
    raise SystemExit

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = 'https://cmanbuildsxyz.com/dude/obs.json'  # Replace with your actual URL

def get_remote_json():
    with urllib.request.urlopen(BASE_URL) as response:
        return json.loads(response.read())

def list_movies():
    movies = get_remote_json()
    for movie in movies:
        list_item = xbmcgui.ListItem(label=movie['item'])
        list_item.setArt({
            'thumb': movie.get('thumbnail', ''),
            'fanart': movie.get('fanart', '')
        })
        url = f"{sys.argv[0]}?action=select_stream&title={urllib.parse.quote(movie['item'])}"
        list_item.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def select_stream(title):
    movies = get_remote_json()
    selected = next((m for m in movies if m['item'] == title), None)
    if not selected:
        xbmcgui.Dialog().ok("Error", "Movie not found.")
        return

    links = selected['link']
    labels = [l['label'] for l in links]
    choice = xbmcgui.Dialog().select(f"Select A Stream For: {title}", labels)
    if choice == -1:
        return

    stream_url = links[choice]['url']
    resolved = resolveurl.resolve(stream_url)
    if not resolved:
        xbmcgui.Dialog().ok("Playback Error", "Unable to resolve link.")
        return

    play_item = xbmcgui.ListItem(path=resolved)
    play_item.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)

def router(paramstring):
    import urllib.parse as urlparse
    params = dict(urlparse.parse_qsl(paramstring))
    action = params.get('action')
    if action == 'select_stream':
        title = params.get('title')
        if title:
            select_stream(title)
    else:
        list_movies()

if __name__ == '__main__':
    router(sys.argv[2][1:])
