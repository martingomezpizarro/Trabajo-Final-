import urllib.request
import re
from html.parser import HTMLParser

try:
    req = urllib.request.Request('https://criptoya.com/charts/riesgo-pais', headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    links = re.findall(r'/api/[^\s\"\'\`]+', html)
    print("Links with /api/:", set(links))
    
    js_files = re.findall(r'src=[\"\']([\w/.-]+.js)[\"\']', html)
    print("JS files:", js_files)
    
except Exception as e:
    print("Error:", e)
