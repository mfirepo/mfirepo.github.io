import sys
import json
import urllib.request
import urllib.parse
import resolveurl
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import resolveurl

EXPECTED_ID = "plugin.video.neocheck"
ADDON = xbmcaddon.Addon()
ACTUAL_ID = ADDON.getAddonInfo("id")
if ACTUAL_ID != EXPECTED_ID:
    xbmcgui.Dialog().ok("Error", "Addon ID mismatch!")
    raise SystemExit

addon = xbmcaddon.Addon()
handle = int(sys.argv[1])

def get_url(**kwargs):
    return sys.argv[0] + '?' + urllib.parse.urlencode(kwargs)

def fetch_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def list_items(json_url):
    items = fetch_json(json_url)
    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setArt({
            'thumb': item.get('thumbnail', ''),
            'fanart': item.get('fanart', '')
        })

        if item.get('is_dir'):
            url = get_url(action='list', url=item['link'])
            is_folder = True
        else:
            url = get_url(action='play', link=item['link'])
            is_folder = False
            list_item.setProperty('IsPlayable', 'true')

        xbmcplugin.addDirectoryItem(handle, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(handle)

def play_video(link):
    resolved = resolveurl.resolve(link)
    if resolved:
        xbmcplugin.setResolvedUrl(handle, True, xbmcgui.ListItem(path=resolved))
    else:
        xbmcgui.Dialog().notification('Error', 'Unable to resolve link', xbmcgui.NOTIFICATION_ERROR)

def router(params):
    if params.get('action') == 'list':
        list_items(params['url'])
    elif params.get('action') == 'play':
        play_video(params['link'])
    else:
        # Set your default remote JSON URL here
        default_url = 'https://cmanbuildsxyz.com/dude/neo.json'
        list_items(default_url)

if __name__ == '__main__':
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    router(params)
