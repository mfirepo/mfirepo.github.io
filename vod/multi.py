# addon.py
import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import sys, json, urllib.request
import resolveurl

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = 'https://cmanbuildsxyz.com/forkq/test.json'  # Replace with your actual URL

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
    choice = xbmcgui.Dialog().select(f"Select Stream for {title}", labels)
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

##############################################################################################

[
  {
    "item": "Ballerina",
    "thumbnail": "https://www.themoviedb.org/t/p/w600_and_h900_bestv2/mKp4euM5Cv3m2U1Vmby3OGwcD5y.jpg",
    "fanart": "https://image.tmdb.org/t/p/original/sItIskd5xpiE64bBWYwZintkGf3.jpg",
    "link": [
      { "label": "1080p", "url": "https://luluvdoo.com/d/o2cd72aeutae" },
      { "label": "1080p", "url": "https://vidmoly.me/w/8sinw3i27cvx" }
    ]
  },
  {
    "item": "Tornado",
    "thumbnail": "https://www.themoviedb.org/t/p/w600_and_h900_bestv2/vRCXxDdAQPjPrJgxKyDyxkb0dDt.jpg",
    "fanart": "https://image.tmdb.org/t/p/original/a94Wn2XksIELb1vSJSMksu1T5G9.jpg",
    "link": [
      { "label": "1080p", "url": "https://vidmoly.me/w/t2e9r0ilvgme" }
    ]
  }
]
