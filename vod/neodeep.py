import sys
import json
import base64
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import xbmcaddon
import resolveurl
from typing import Dict, List

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
PLUGIN_KEY = "plugin.video.neo_flix"
DEFAULT_JSON_URL = "https://cmanbuildsxyz.com/dude/neo.json"
HANDLE = int(sys.argv[1])

def log(message: str, level=xbmc.LOGINFO) -> None:
    xbmc.log(f"[{ADDON_NAME}] {message}", level)

def get_url(**kwargs: Dict[str, str]) -> str:
    return f"{sys.argv[0]}?{urllib.parse.urlencode(kwargs)}"

def fetch_json(url: str) -> List[Dict]:
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        log(f"Failed to fetch JSON from {url}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Connection Error', 'Failed to fetch content. Check your internet.', xbmcgui.NOTIFICATION_ERROR)
    except json.JSONDecodeError as e:
        log(f"Invalid JSON from {url}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Data Error', 'Invalid content received from server.', xbmcgui.NOTIFICATION_ERROR)
    return []

def encrypt(text: str, key: str) -> str:
    encrypted_bytes = bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(text)])
    return base64.urlsafe_b64encode(encrypted_bytes).decode()

def decrypt(encrypted_text: str, key: str) -> str:
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_chars = [chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(encrypted_bytes)]
        return ''.join(decrypted_chars)
    except Exception as e:
        log(f"Decryption failed: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Decryption Error', 'Failed to decode stream URL.', xbmcgui.NOTIFICATION_ERROR)
        return ""

def list_items(json_url: str) -> None:
    items = fetch_json(decrypt(json_url, ADDON_ID))
    if not items:
        xbmcgui.Dialog().notification('No Content', 'No items found in the list.', xbmcgui.NOTIFICATION_INFO)
        return

    for item in items:
        title = item.get('title', 'Untitled')
        summary = item.get('summary', 'No description available.')
        thumbnail = item.get('thumbnail', '')
        fanart = item.get('fanart', '')

        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'thumb': thumbnail, 'fanart': fanart})
        list_item.setInfo('video', {'title': title, 'plot': summary})

        if item.get('is_dir', False):
            url = get_url(action='list', url=encrypt(item['link'], PLUGIN_KEY))
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
        elif item.get('link') == 'magnet:':
            url = get_url(action='no_link')
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)
        elif 'links' in item and isinstance(item['links'], list):
            encoded_links = encrypt(json.dumps(item['links']), PLUGIN_KEY)
            url = get_url(action='choose_stream', urls=encoded_links)
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)
        elif 'link' in item:
            url = get_url(action='play', url=encrypt(item['link'], ADDON_ID))
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(link: str) -> None:
    url = decrypt(link, ADDON_ID)
    if not url:
        return

    if url.endswith('.m3u8'):
        item = xbmcgui.ListItem(path=url)
        item.setMimeType('application/vnd.apple.mpegurl')
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.setResolvedUrl(HANDLE, True, item)
    else:
        try:
            resolved_url = resolveurl.resolve(url)
            if resolved_url:
                item = xbmcgui.ListItem(path=resolved_url)
                xbmcplugin.setResolvedUrl(HANDLE, True, item)
            else:
                raise Exception("ResolveURL failed")
        except Exception as e:
            log(f"Failed to resolve URL {url}: {e}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('Playback Error', 'Could not play this stream.', xbmcgui.NOTIFICATION_ERROR)

def choose_and_play_stream(encrypted_json: str) -> None:
    try:
        decrypted = decrypt(encrypted_json, PLUGIN_KEY)
        streams = json.loads(decrypted)
        if not streams:
            raise ValueError("No streams available")

        if len(streams) == 1:
            play_video(encrypt(streams[0]['url'], ADDON_ID))
            return

        dialog = xbmcgui.Dialog()
        stream_labels = []
        for i, stream in enumerate(streams):
            label = stream.get('label', f'Stream {i+1}')
            quality = stream.get('quality', '')
            if quality:
                label = f"{label} ({quality})"
            stream_labels.append(label)

        selected = dialog.select("Choose Stream Quality", stream_labels)
        
        if selected >= 0:
            play_video(encrypt(streams[selected]['url'], ADDON_ID))
    except Exception as e:
        log(f"Stream selection failed: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Selection Error', 'Failed to choose a stream.', xbmcgui.NOTIFICATION_ERROR)

def router(params: Dict[str, str]) -> None:
    action = params.get('action', '')
    url = params.get('url', '')
    urls = params.get('urls', '')

    if action == 'list' and url:
        list_items(url)
    elif action == 'play' and url:
        play_video(url)
    elif action == 'choose_stream' and urls:
        choose_and_play_stream(urls)
    elif action == 'no_link':
        xbmcgui.Dialog().notification('No Stream', 'This item is not playable.', xbmcgui.NOTIFICATION_INFO)
    else:
        default_url = encrypt(DEFAULT_JSON_URL, PLUGIN_KEY)
        list_items(default_url)

if __name__ == '__main__':
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    router(params)
