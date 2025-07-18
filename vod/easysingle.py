import xbmcplugin, xbmcgui, xbmcaddon, xbmc
import sys, json, urllib.request, urllib.parse
import resolveurl
import os

EXPECTED_ID = "plugin.video.easyflix"
ADDON = xbmcaddon.Addon()
ACTUAL_ID = ADDON.getAddonInfo("id")
if ACTUAL_ID != EXPECTED_ID:
    xbmcgui.Dialog().ok("Error", "Addon ID Mismatch!")
    raise SystemExit

HANDLE = int(sys.argv[1])
DEFAULT_URL = 'https://cmanbuildsxyz.com/dude/easy.json'

def get_remote_json(url):
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        xbmcgui.Dialog().ok("Network Error", f"Failed to load content:\n{str(e)}")
        return []

def list_directory(url):
    items = get_remote_json(url)
    for entry in items:
        if entry.get("type") == "folder":
            folder_name = entry["name"]
            folder_url = entry["url"]
            list_item = xbmcgui.ListItem(label=folder_name)
            list_item.setArt({
                'thumb': entry.get('thumbnail', ''),
                'fanart': entry.get('fanart', '')
            })
            folder_query = f"{sys.argv[0]}?action=list_directory&url={urllib.parse.quote(folder_url)}"
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=folder_query, listitem=list_item, isFolder=True)

        elif entry.get("type") == "movie":
            list_item = xbmcgui.ListItem(label=entry['item'])
            list_item.setArt({
                'thumb': entry.get('thumbnail', ''),
                'fanart': entry.get('fanart', '')
            })
            movie_title = entry['item']
            base64_movie = urllib.parse.quote(json.dumps(entry))  # Encode full movie entry
            url = f"{sys.argv[0]}?action=select_stream&data={base64_movie}"
            list_item.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def select_stream(encoded_movie_data):
    try:
        movie = json.loads(urllib.parse.unquote(encoded_movie_data))
    except:
        xbmcgui.Dialog().ok("Error", "Invalid movie data.")
        return

    links = movie.get("link", [])

    # If only one stream link, play immediately
    if len(links) == 1:
        stream_url = links[0]["url"]
    else:
        labels = [l["label"] for l in links]
        choice = xbmcgui.Dialog().select(f"Select A Stream For: {movie['item']}", labels)
        if choice == -1:
            return
        stream_url = links[choice]["url"]

    # Check if it's a direct .m3u8 stream
    if stream_url.endswith(".m3u8"):
        final_url = stream_url
    else:
        # Use resolveurl for other links
        final_url = resolveurl.resolve(stream_url)
        if not final_url:
            xbmcgui.Dialog().ok("Playback Error", "Unable to resolve link.")
            return

    play_item = xbmcgui.ListItem(path=final_url)
    play_item.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)

def router(paramstring):
    import urllib.parse as urlparse
    params = dict(urlparse.parse_qsl(paramstring))
    action = params.get("action")
    if action == "list_directory":
        url = params.get("url", DEFAULT_URL)
        list_directory(url)
    elif action == "select_stream":
        data = params.get("data")
        if data:
            select_stream(data)
    else:
        list_directory(DEFAULT_URL)

if __name__ == "__main__":
    router(sys.argv[2][1:])

