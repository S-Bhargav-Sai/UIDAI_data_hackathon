import json
import urllib.request

url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
try:
    with urllib.request.urlopen(url) as response:
        data = json.load(response)
        
    names = sorted([f['properties']['ST_NM'] for f in data['features']])
    print("GeoJSON State Names:")
    for n in names:
        print(n)
        
except Exception as e:
    print(e)
