###########################################
#     GIVE CREDIT WHERE CREDIT IS DUE     #
#                                         #
#          T4ILS AND JETJET               #
###########################################




import json, sys, time, operator, os, requests,base64
from ..util.dialogs import link_dialog
from xbmcvfs import translatePath
from concurrent.futures import ThreadPoolExecutor
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
from resources.lib.plugin import Plugin
from datetime import datetime, timedelta, timezone
import calendar, inputstreamhelper
from jetextractors import extractor
from resources.lib.plugin import run_hook
import urllib.parse

import operator, traceback
PROGRESS = xbmcgui.DialogProgress()
CACHE_TIME = 0  # change to wanted cache time in seconds

addon_fanart = xbmcaddon.Addon().getAddonInfo('fanart')
addon_icon = xbmcaddon.Addon().getAddonInfo('icon')

class DirectSearch(Plugin):
    name = "pvr_sport_search"
    priority = 100

    def get_cache_path(self) -> str:
        user_path = translatePath(xbmcaddon.Addon().getAddonInfo("profile")) or "."
        config_path = os.path.join(user_path, f"{self.name}_cache.json")
        return config_path

    @property
    def search_include(self):
        r = requests.get(base64.b64decode("aHR0cHM6Ly9tYWduZXRpYy53ZWJzaXRlL01BRF9USVRBTl9TUE9SVFMvc2VhcmNoX2luY2x1ZGUvc2VhcmNoX2luY2x1ZGUuanNvbg==").decode("utf-8")).json()
        return r
    
    def process_item(self, item):
        if self.name in item:
            link = item.get(self.name, "")
            thumbnail = item.get("thumbnail", "")
            fanart = item.get("fanart", "")
            icon = item.get("icon", "")
            if link.startswith("search") or link.startswith("cache") or link.startswith("clear"):
                item["is_dir"] = True
                item["link"] = f"{self.name}/{link}"
                list_item = xbmcgui.ListItem(item.get("title", item.get("name", "")), offscreen=True)
                list_item.setArt({"thumb": thumbnail, "fanart": fanart})
                item["list_item"] = list_item
                return item
            
    def save_to_cache(self, query, jen_list):
        cache_path = self.get_cache_path()
        if not os.path.exists(cache_path):
            cache = []
        else:
            with open(cache_path, "r+") as f:
                cache = json.load(f)
        entry = {
            "query": query,
            "time": int(datetime.now(timezone.utc).timestamp()),
            "items": jen_list
        }
        cache.insert(0, entry)
        if len(cache) > 10:
            cache.pop()
        with open(cache_path, "w") as f:
            json.dump(cache, f)

    def search_extractors(self, query, include: str) -> list:
        progress = xbmcgui.DialogProgress()
        progress.create("Searching extractors...")
        progress.update(0, "Please wait while links are being searched.\nThis could take several seconds.\n0% (0 links)")
        start_time = time.time()
        def callback(prog):
            percentage = int((prog.total - len(prog.extractors)) / prog.total * 100)
            message = f"Please wait while links are being searched.\nThis could take several seconds.\n{percentage}% ({prog.links} links)"
            if time.time() - start_time > 3:
                message += f"\nWaiting for: {', '.join(prog.extractors)}"
            progress.update(percentage, message)
            if progress.iscanceled():
                prog.event.set()
        games = extractor.search_extractors(query, include=self.search_include.get("search_include" + include, None), progress=callback)
        xbmc.sleep(500)
        progress.close()
        empty_date = datetime(year=2030, month=12, day=31)
        jen_list = []
        for game in games:
            jen_data = {
                "title": "[COLORdodgerblue]%s[COLORwhite] |[B][I] %s[/B][/I]\n  [COLORred]%s | %s[/COLOR]" % (game.league.replace("'", "") if game.league is not None else "", game.title, game.extractor, format_time(game.starttime)),
                "thumbnail": game.icon,
                "fanart": game.icon,
                "summary": game.title,
                "sportjetextractors": [link.to_dict() for link in game.links],
                "time": game.starttime.timestamp() if game.starttime != None else empty_date.timestamp(),
                "type": "item"
            }
            jen_list.append(jen_data)
        self.save_to_cache(query, jen_list)
        return jen_list
        
            
    def routes(self, plugin):
        @plugin.route(f"/{self.name}/search/<path:query>")
        def search(query):
            query = urllib.parse.unquote_plus(query)
            if query == "*":
                query = xbmcgui.Dialog().input("Search game")
                if query == "": return
            if "include" in plugin.args:
                include = plugin.args["include"][0]
            else:
                include = ""
            jen_list = self.search_extractors(query, include)
            jen_list = sorted(jen_list, key=lambda x: x["time"])
            jen_list = [run_hook("process_item", item) for item in jen_list]
            jen_list = [run_hook("get_metadata", item, return_item_on_failure=True) for item in jen_list]
            run_hook("display_list", jen_list)

        @plugin.route(f"/{self.name}/search_dialog/<path:query>")
        def search_dialog(query):
            query = urllib.parse.unquote_plus(query)
            if query == "*":
                query = xbmcgui.Dialog().input("Search game")
                if query == "": return
            if "include" in plugin.args:
                include = plugin.args["include"][0]
            else:
                include = ""
            if "include" in plugin.args:
                include = plugin.args["include"][0]
            else:
                include = ""
            jen_list = self.search_extractors(query, include)
            idx = link_dialog([game["title"] for game in jen_list], return_idx=True, hide_links=False)
            if idx == None:
                return True
            run_hook("play_video", json.dumps(jen_list[idx]))
        
        @plugin.route(f"/{self.name}/cache")
        def cache():
            cache_path = self.get_cache_path()
            jen_list = []
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    items = json.load(f)
                for i, item in enumerate(items):
                    jen_list.append({
                        "title": f"Query:[COLORred] {item['query'].upper()}[/COLOR] [COLORyellow]  ({len(item['items'])} links)[/COLOR]\nTime: {datetime.fromtimestamp(item['time']).strftime('%m/%d %I:%M %p')}",
                        "type": "dir",
                        self.name: f"cache/{i}"
                    })
            jen_list = [run_hook("process_item", item) for item in jen_list]
            jen_list = [run_hook("get_metadata", item, return_item_on_failure=True) for item in jen_list]
            run_hook("display_list", jen_list)

        @plugin.route(f"/{self.name}/cache/<entry>")
        def cache_entry(entry):
            entry = int(entry)
            cache_path = self.get_cache_path()
            with open(cache_path, "r") as f:
                items = json.load(f)
            jen_list = items[entry]["items"]
            jen_list = [run_hook("process_item", item) for item in jen_list]
            jen_list = [run_hook("get_metadata", item, return_item_on_failure=True) for item in jen_list]
            run_hook("display_list", jen_list)

        @plugin.route(f"/{self.name}/clear")
        def clear():
            addon = xbmcaddon.Addon()
            USER_DATA_DIR = translatePath(addon.getAddonInfo("profile"))
            if os.path.exists(os.path.join(USER_DATA_DIR, f"{self.name}_cache.json")):
                os.remove(os.path.join(USER_DATA_DIR, f"{self.name}_cache.json"))
            xbmcgui.Dialog().ok("Clear", "You are now [COLORred]clearing[/COLOR] your previous searches.")



def format_time(date):
    return utc_to_local(date).strftime("%m/%d %I:%M %p") if date != None else ""

# https://stackoverflow.com/questions/4563272/convert-a-python-utc-datetime-to-a-local-datetime-using-only-python-standard-lib
def utc_to_local(utc_dt):
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)