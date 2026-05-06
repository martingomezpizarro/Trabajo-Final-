import requests
import json
import urllib3
import traceback
urllib3.disable_warnings()

try:
    url = 'https://api.bcra.gob.ar/estadisticas/v2.0/PrincipalesVariables'
    r = requests.get(url, headers={'Accept': 'application/json'}, verify=False, timeout=30)
    data = r.json()
    with open("bcra_vars.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("BCRA Guardado exitosamente!")
except Exception as e:
    with open("bcra_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Error en BCRA.")
