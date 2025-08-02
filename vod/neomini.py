import sys, json, base64, urllib.request, urllib.parse, xbmcplugin, xbmcgui, xbmcaddon, resolveurl

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
PLUGIN_KEY = "plugin.video.neo_flix"
DEFAULT_JSON_URL = "https://bitbucket.org/halcyonhal/easy_neo/raw/main/neo.json"
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

def list_items(json_url: str) -> None:
    items = fetch_json(decrypt(json_url, ADDON_ID))
    for item in items:
        is_folder = bool(item.get('is_dir'))
        list_item = xbmcgui.ListItem(label=item.get('title', 'Untitled'))
        list_item.setArt({'thumb': item.get('thumbnail', ''), 'fanart': item.get('fanart', '')})
        if is_folder:
            url = get_url(action='list', url=encrypt(item['link'], PLUGIN_KEY))
        elif item.get('link') == 'magnet:':
            url = get_url(action='no_link')
        elif 'links' in item and isinstance(item['links'], list):
            encoded_links = encrypt(json.dumps(item['links']), PLUGIN_KEY)
            url = get_url(action='choose_stream', urls=encoded_links)
            list_item.setProperty('IsPlayable', 'true')
        elif 'link' in item:
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
        default_url = encrypt(DEFAULT_JSON_URL, PLUGIN_KEY)
        list_items(default_url)

if __name__ == '__main__':
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    router(params)
