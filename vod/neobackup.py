import sys
import json
import urllib.parse
import urllib.request
import xbmcplugin
import xbmcgui
import xbmcaddon
import resolveurl
import os

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# Update this to your actual JSON or M3U URL
REMOTE_PLAYLIST_URL = "https://cmanbuildsxyz.com/forkq/test.json"


def get_url(params):
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def fetch_remote_data(url):
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode()
            if url.endswith(".m3u"):
                return parse_m3u(content)
            return json.loads(content)
    except Exception as e:
        xbmcgui.Dialog().notification("Error", str(e), xbmcgui.NOTIFICATION_ERROR)
        return []


def parse_m3u(content):
    items = []
    lines = content.splitlines()
    title, thumb = None, None
    for line in lines:
        if line.startswith("#EXTINF:"):
            parts = line.split(",")
            title = parts[-1].strip()
            if "tvg-logo=" in line:
                thumb = line.split('tvg-logo="')[1].split('"')[0]
        elif line and not line.startswith("#"):
            items.append({
                "title": title or line,
                "link": line,
                "thumbnail": thumb,
                "type": "video"
            })
            title, thumb = None, None
    return items


def list_items():
    items = fetch_remote_data(REMOTE_PLAYLIST_URL)
    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        thumb = item.get('thumbnail')
        fanart = item.get('fanart') or thumb
        if thumb:
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': fanart})
        if item.get('type') == 'dir':
            url = get_url({'action': 'dir', 'url': item['link']})
            is_folder = True
        else:
            url = get_url({'action': 'play', 'url': item['link']})
            is_folder = False
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=is_folder)
    xbmcplugin.endOfDirectory(HANDLE)


def list_directory(url):
    items = fetch_remote_data(url)
    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        thumb = item.get('thumbnail')
        fanart = item.get('fanart') or thumb
        if thumb:
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': fanart})
        list_item.setProperty('IsPlayable', 'true')
        play_url = get_url({'action': 'play', 'url': item['link']})
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)


def play_video(url):
    resolved = resolveurl.resolve(url)
    if not resolved:
        xbmcgui.Dialog().notification("ResolveURL", "Failed to resolve link", xbmcgui.NOTIFICATION_ERROR)
        return
    play_item = xbmcgui.ListItem(path=resolved)
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


if __name__ == '__main__':
    args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    action = args.get('action')
    url = args.get('url')

    if action == 'play':
        play_video(url)
    elif action == 'dir':
        list_directory(url)
    else:
        list_items()

#############################################################################################
[
  {
    "title": "Free Movies",
    "link": "https://cmanbuildsxyz.com/forkq/vodu.json",
    "thumbnail": "https://archive.org/download/icon_20250528/icon.png",
    "fanart": "https://archive.org/download/background_20250524/Background.jpg",
    "type": "dir"
  },
  {
    "title": "Debrid Movies",
    "link": "https://cmanbuildsxyz.com/forkq/vodmu.json",
    "thumbnail": "https://archive.org/download/icon_20250528/icon.png",
    "fanart": "https://archive.org/download/background_20250524/Background.jpg",
    "type": "dir"
  }
 
]
