import sys
import json
import base64
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import xbmcaddon
import resolveurl

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
handle = int(sys.argv[1])

def get_url(**kwargs):
    return sys.argv[0] + '?' + urllib.parse.urlencode(kwargs)

def fetch_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def list_items(json_url):
    items = fetch_json(decrypt(json_url, addon_id))
    for item in items:
        is_folder = False
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setArt({
            'thumb': item.get('thumbnail', ''),
            'fanart': item.get('fanart', '')
        })

        if item.get('is_dir'):
            url = get_url(action='list', url=encrypt(item['link'], 'plugin.video.neo_flix'))
            is_folder = True
        elif item['link'] == 'magnet:':
            url = get_url(action='no_link')
        else:
            url = get_url(action='play', url=encrypt(item['link'], 'plugin.video.neo_flix'))
            list_item.setProperty('IsPlayable', 'true')

        xbmcplugin.addDirectoryItem(handle, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(handle)

def play_video(link):
    resolved = resolveurl.resolve(decrypt(link, addon_id))
    if resolved:
        xbmcplugin.setResolvedUrl(handle, True, xbmcgui.ListItem(path=resolved))
    else:
        xbmcgui.Dialog().notification('Error', 'Unable to resolve link', xbmcgui.NOTIFICATION_ERROR)


def encrypt(text: str, key: str) -> str:
    """Encrypts a string using XOR and a personal key."""
    encrypted_bytes = bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(text)])
    return base64.urlsafe_b64encode(encrypted_bytes).decode()

def decrypt(encrypted_text: str, key: str) -> str:
    """Decrypts a string encrypted with the encrypt() function."""
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
    decrypted_chars = [chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(encrypted_bytes)]
    return ''.join(decrypted_chars)


def router(params):
    url = params.get('url')
    action = params.get('action')
    if action == 'list':
        list_items(url)
    elif action == 'no_link':
        sys.exit()
    elif action == 'play':
        play_video(url)
    else:
        # Set your default remote JSON URL here
        default_url = encrypt('https://cmanbuildsxyz.com/neo/neo.json', 'plugin.video.neo_flix')
        list_items(default_url)

if __name__ == '__main__':
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    router(params)
    
