import sys
import urllib.parse
import xbmcplugin
import xbmcgui
import xbmcaddon
import json
import requests
import resolveurl

addon = xbmcaddon.Addon()
handle = int(sys.argv[1])

BASE_URL = 'https://cmanbuildsxyz.com/forkq/neo.json'

def build_url(query):
    return sys.argv[0] + '?' + urllib.parse.urlencode(query)

def list_items(items):
    for item in items:
        item_type = item.get('type', 'video')
        title = item.get('title', 'No Title')
        thumbnail = item.get('thumbnail', '')
        fanart = item.get('fanart', '')
        
        if item_type == 'dir':
            url = build_url({'action': 'dir', 'items': json.dumps(item.get('items', []))})
            list_item = xbmcgui.ListItem(label=title)
            list_item.setArt({'thumb': thumbnail, 'fanart': fanart})
            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=True)
        elif item_type == 'video':
            url = build_url({'action': 'play', 'url': item['url']})
            list_item = xbmcgui.ListItem(label=title)
            list_item.setArt({'thumb': thumbnail, 'fanart': fanart})
            list_item.setInfo('video', {'title': title})
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def play_item(url):
    resolved_url = resolveurl.resolve(url)
    if resolved_url:
        xbmcplugin.setResolvedUrl(handle, True, xbmcgui.ListItem(path=resolved_url))
    else:
        xbmcgui.Dialog().notification('ResolveURL', 'Failed to resolve URL', xbmcgui.NOTIFICATION_ERROR)

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')

    if action == 'play':
        play_item(params['url'])
    elif action == 'dir':
        items = json.loads(params['items'])
        list_items(items)
    else:
        try:
            response = requests.get(BASE_URL)
            items = response.json()
            list_items(items)
        except Exception as e:
            xbmcgui.Dialog().notification('Remote JSON', f'Error loading data: {e}', xbmcgui.NOTIFICATION_ERROR)

if __name__ == '__main__':
    router(sys.argv[2][1:])
