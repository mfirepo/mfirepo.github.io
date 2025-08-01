import sys
import json
import base64
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import xbmcaddon
import resolveurl

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
PLUGIN_KEY = "plugin.video.neo_flix"
ROOT_JSON_URL = "https://bitbucket.org/halcyonhal/easy_neo/raw/main/menu.json"
HANDLE = int(sys.argv[1])

def get_url(**kwargs) -> str:
    return f"{sys.argv[0]}?{urllib.parse.urlencode(kwargs)}"

def fetch_json(url: str) -> list:
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        xbmcgui.Dialog().notification('Error', f'Failed to fetch JSON: {e}', xbmcgui.NOTIFICATION_ERROR)
        return []

def list_items(json_url: str = None, is_root=False) -> None:
    if is_root:
        sources = fetch_json(ROOT_JSON_URL)
        for source in sources:
            title = source.get("title", "Untitled Source")
            url = source.get("url")
            thumb = source.get("thumbnail", "")
            fanart = source.get("fanart", "")
            if not url:
                continue
            enc_url = encrypt(url, PLUGIN_KEY)
            list_item = xbmcgui.ListItem(label=title)
            list_item.setArt({'thumb': thumb, 'fanart': fanart})
            action_url = get_url(action="list", url=enc_url)
            xbmcplugin.addDirectoryItem(HANDLE, action_url, list_item, True)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    items = fetch_json(decrypt(json_url, ADDON_ID))
    for item in items:
        is_folder = bool(item.get('is_dir'))
        list_item = xbmcgui.ListItem(label=item.get('title', item.get('item', 'Untitled')))
        list_item.setArt({
            'thumb': item.get('thumbnail', ''),
            'fanart': item.get('fanart', '')
        })

        if isinstance(item.get('link'), list):
            links = []
            for link_entry in item['link']:
                label = link_entry.get('label', 'Link')
                url = link_entry.get('url')
                if url:
                    links.append({'label': label, 'url': url})
            if links:
                encoded_links = encrypt(json.dumps(links), PLUGIN_KEY)
                url = get_url(action='choose_stream', urls=encoded_links)
                list_item.setProperty('IsPlayable', 'true')
            else:
                continue

        elif 'links' in item and isinstance(item['links'], list):
            encoded_links = encrypt(json.dumps(item['links']), PLUGIN_KEY)
            url = get_url(action='choose_stream', urls=encoded_links)
            list_item.setProperty('IsPlayable', 'true')

        elif 'link' in item and isinstance(item['link'], str):
            if item['link'] == 'magnet:':
                url = get_url(action='no_link')
            elif is_folder:
                url = get_url(action='list', url=encrypt(item['link'], PLUGIN_KEY))
            else:
                url = get_url(action='play', url=encrypt(item['link'], PLUGIN_KEY))
                list_item.setProperty('IsPlayable', 'true')
        else:
            continue

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(HANDLE)

def play_video(link: str) -> None:
    try:
        url = decrypt(link, ADDON_ID)
    except Exception as e:
        xbmcgui.Dialog().notification('Error', f'Failed to decrypt link: {e}', xbmcgui.NOTIFICATION_ERROR)
        return

    if url.endswith('.m3u8'):
        item = xbmcgui.ListItem(path=url)
        item.setMimeType('application/vnd.apple.mpegurl')
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.setResolvedUrl(HANDLE, True, item)
    else:
        resolved = resolveurl.resolve(url)
        if resolved:
            xbmcplugin.setResolvedUrl(HANDLE, True, xbmcgui.ListItem(path=resolved))
        else:
            xbmcgui.Dialog().notification('Error', 'Unable to resolve link', xbmcgui.NOTIFICATION_ERROR)

def choose_and_play_stream(encrypted_json: str) -> None:
    try:
        decrypted = decrypt(encrypted_json, PLUGIN_KEY)
        streams = json.loads(decrypted)

        if not streams:
            raise ValueError("Empty stream list")

        if len(streams) == 1:
            play_video(encrypt(streams[0]['url'], ADDON_ID))
            return

        labels = [s.get('label', f"Stream {i + 1}") for i, s in enumerate(streams)]
        index = xbmcgui.Dialog().select("Choose A Stream", labels)
        if index == -1:
            return

        selected_url = streams[index]['url']
        play_video(encrypt(selected_url, ADDON_ID))

    except Exception as e:
        xbmcgui.Dialog().notification('Error', f'Stream selection failed: {e}', xbmcgui.NOTIFICATION_ERROR)

def encrypt(text: str, key: str) -> str:
    encrypted_bytes = bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(text)])
    return base64.urlsafe_b64encode(encrypted_bytes).decode()

def decrypt(encrypted_text: str, key: str) -> str:
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_chars = [chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(encrypted_bytes)]
        return ''.join(decrypted_chars)
    except Exception as e:
        xbmcgui.Dialog().notification('Error', f'Decryption failed: {e}', xbmcgui.NOTIFICATION_ERROR)
        return ''

def router(params: dict) -> None:
    action = params.get('action', '')
    url = params.get('url')
    urls = params.get('urls')

    if action == 'list' and url:
        list_items(url)
    elif action == 'play' and url:
        play_video(url)
    elif action == 'choose_stream' and urls:
        choose_and_play_stream(urls)
    elif action == 'no_link':
        xbmcgui.Dialog().notification('Notice', 'No stream available.', xbmcgui.NOTIFICATION_INFO)
    else:
        list_items(is_root=True)

if __name__ == '__main__':
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    router(params)
