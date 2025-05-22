import sys
import json
import urllib.request
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import resolveurl

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = urllib.parse.parse_qs(sys.argv[2][1:])

# 🔗 Replace with your JSON URL
JSON_URL = 'https://cmanbuildsxyz.com/forkq/vodu.json'

def get_videos():
    try:
        with urllib.request.urlopen(JSON_URL) as response:
            return json.load(response)
    except Exception as e:
        xbmc.log(f"Failed to fetch JSON: {e}", xbmc.LOGERROR)
        return []

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def list_videos():
    videos = get_videos()
    for item in videos:
        url = build_url({'action': 'play', 'link': item['link']})
        li = xbmcgui.ListItem(label=item['title'])
        li.setArt({
            'thumb': item.get('thumbnail', ''),
            'fanart': item.get('fanart', ''),
            'icon': item.get('thumbnail', '')
        })
        li.setInfo('video', {'title': item['title']})
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(addon_handle)

def play_video(link):
    resolved = resolveurl.resolve(link)
    if resolved:
        li = xbmcgui.ListItem(path=resolved)
        li.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(addon_handle, True, li)
    else:
        xbmcgui.Dialog().notification('ResolveURL Failed', 'Could not resolve link.', xbmcgui.NOTIFICATION_ERROR)

def router(params):
    if params.get('action') == ['play'] and 'link' in params:
        play_video(params['link'][0])
    else:
        list_videos()

if __name__ == '__main__':
    router(args)
