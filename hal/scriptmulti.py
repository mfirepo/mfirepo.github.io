import sys
import json
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import resolveurl

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = urllib.parse.parse_qs(sys.argv[2][1:])

JSON_URL = 'https://cmanbuildsxyz.com/forkq/test.json'  # Replace with your remote JSON

def get_remote_data(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def list_videos():
    items = get_remote_data(JSON_URL)
    for i, video in enumerate(items):
        url = build_url({'action': 'select_source', 'idx': i})
        li = xbmcgui.ListItem(label=video['title'])
        li.setArt({'thumb': video['thumbnail'], 'fanart': video['fanart']})
        li.setInfo('video', {'title': video['title']})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def select_source(idx):
    items = get_remote_data(JSON_URL)
    video = items[int(idx)]
    for link in video['links']:
        resolved = resolveurl.resolve(link)
        if resolved:
            li = xbmcgui.ListItem(label='[COLORlime]Play 1080p[/COLOR]')
            li.setArt({'thumb': video['thumbnail'], 'fanart': video['fanart']})
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=build_url({'action': 'play', 'url': link}), listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)

def play_video(url):
    resolved = resolveurl.resolve(url)
    if resolved:
        li = xbmcgui.ListItem(path=resolved)
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

if __name__ == '__main__':
    action = args.get('action', [None])[0]

    if action is None:
        list_videos()
    elif action == 'select_source':
        select_source(args['idx'][0])
    elif action == 'play':
        play_video(args['url'][0])
