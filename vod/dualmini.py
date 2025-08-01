import sys,json,base64,urllib.request,urllib.parse,xbmcplugin,xbmcgui,xbmcaddon,resolveurl
ADDON=xbmcaddon.Addon()
ADDON_ID=ADDON.getAddonInfo('id')
PLUGIN_KEY="plugin.video.neo_flix"
ROOT_JSON_URL="https://bitbucket.org/halcyonhal/easy_neo/raw/main/menu.json"
HANDLE=int(sys.argv[1])
def get_url(**kwargs):return f"{sys.argv[0]}?{urllib.parse.urlencode(kwargs)}"
def fetch_json(url): 
 try:with urllib.request.urlopen(url) as r:return json.loads(r.read().decode())
 except Exception as e:xbmcgui.Dialog().notification('Error',f'Failed to fetch JSON: {e}',xbmcgui.NOTIFICATION_ERROR);return []
def list_items(json_url=None,is_root=False):
 if is_root:
  sources=fetch_json(ROOT_JSON_URL)
  for s in sources:
   title=s.get("title","Untitled Source")
   url=s.get("url")
   thumb=s.get("thumbnail","")
   fanart=s.get("fanart","")
   if not url:continue
   enc_url=encrypt(url,PLUGIN_KEY)
   li=xbmcgui.ListItem(label=title)
   li.setArt({'thumb':thumb,'fanart':fanart})
   xbmcplugin.addDirectoryItem(HANDLE,get_url(action="list",url=enc_url),li,True)
  xbmcplugin.endOfDirectory(HANDLE);return
 items=fetch_json(decrypt(json_url,ADDON_ID))
 for i in items:
  is_folder=bool(i.get('is_dir'))
  li=xbmcgui.ListItem(label=i.get('title',i.get('item','Untitled')))
  li.setArt({'thumb':i.get('thumbnail',''),'fanart':i.get('fanart','')})
  if isinstance(i.get('link'),list):
   links=[]
   for l in i['link']:
    label=l.get('label','Link')
    url=l.get('url')
    if url:links.append({'label':label,'url':url})
   if links:
    encoded=encrypt(json.dumps(links),PLUGIN_KEY)
    url=get_url(action='choose_stream',urls=encoded)
    li.setProperty('IsPlayable','true')
   else:continue
  elif 'links' in i and isinstance(i['links'],list):
   encoded=encrypt(json.dumps(i['links']),PLUGIN_KEY)
   url=get_url(action='choose_stream',urls=encoded)
   li.setProperty('IsPlayable','true')
  elif 'link' in i and isinstance(i['link'],str):
   if i['link']=='magnet:':url=get_url(action='no_link')
   elif is_folder:url=get_url(action='list',url=encrypt(i['link'],PLUGIN_KEY))
   else:
    url=get_url(action='play',url=encrypt(i['link'],PLUGIN_KEY))
    li.setProperty('IsPlayable','true')
  else:continue
  xbmcplugin.addDirectoryItem(HANDLE,url,li,is_folder)
 xbmcplugin.endOfDirectory(HANDLE)
def play_video(link):
 try:url=decrypt(link,ADDON_ID)
 except Exception as e:xbmcgui.Dialog().notification('Error',f'Failed to decrypt link: {e}',xbmcgui.NOTIFICATION_ERROR);return
 if url.endswith('.m3u8'):
  item=xbmcgui.ListItem(path=url)
  item.setMimeType('application/vnd.apple.mpegurl')
  item.setProperty('IsPlayable','true')
  xbmcplugin.setResolvedUrl(HANDLE,True,item)
 else:
  resolved=resolveurl.resolve(url)
  if resolved:xbmcplugin.setResolvedUrl(HANDLE,True,xbmcgui.ListItem(path=resolved))
  else:xbmcgui.Dialog().notification('Error','Unable to resolve link',xbmcgui.NOTIFICATION_ERROR)
def choose_and_play_stream(encrypted_json):
 try:
  decrypted=decrypt(encrypted_json,PLUGIN_KEY)
  streams=json.loads(decrypted)
  if not streams:raise ValueError("Empty stream list")
  if len(streams)==1:play_video(encrypt(streams[0]['url'],ADDON_ID));return
  labels=[s.get('label',f"Stream {i+1}") for i,s in enumerate(streams)]
  index=xbmcgui.Dialog().select("Choose A Stream",labels)
  if index==-1:return
  play_video(encrypt(streams[index]['url'],ADDON_ID))
 except Exception as e:xbmcgui.Dialog().notification('Error',f'Stream selection failed: {e}',xbmcgui.NOTIFICATION_ERROR)
def encrypt(text,key):return base64.urlsafe_b64encode(bytes([ord(c)^ord(key[i%len(key)]) for i,c in enumerate(text)])).decode()
def decrypt(enc,key):
 try:
  eb=base64.urlsafe_b64decode(enc.encode())
  return ''.join([chr(b^ord(key[i%len(key)])) for i,b in enumerate(eb)])
 except Exception as e:xbmcgui.Dialog().notification('Error',f'Decryption failed: {e}',xbmcgui.NOTIFICATION_ERROR);return ''
def router(params):
 action=params.get('action','')
 url=params.get('url')
 urls=params.get('urls')
 if action=='list' and url:list_items(url)
 elif action=='play' and url:play_video(url)
 elif action=='choose_stream' and urls:choose_and_play_stream(urls)
 elif action=='no_link':xbmcgui.Dialog().notification('Notice','No stream available.',xbmcgui.NOTIFICATION_INFO)
 else:list_items(is_root=True)
if __name__=='__main__':
 params=dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
 router(params)
