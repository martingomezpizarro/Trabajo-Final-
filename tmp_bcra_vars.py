"""Script temporal para listar variables de la API del BCRA"""
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = 'https://api.bcra.gob.ar/estadisticas/v2.0/PrincipalesVariables'
headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}

try:
    r = requests.get(url, headers=headers, verify=False, timeout=30)
    r.raise_for_status()
    data = r.json()
    results = data.get('results', [])
    print(f"Total variables: {len(results)}")
    print("-" * 80)
    for v in results:
        desc = v.get('descripcion', '')
        vid = v.get('idVariable', '')
        # Filtrar por depositos o dolares
        if any(kw in desc.lower() for kw in ['depósito', 'deposito', 'dólar', 'dolar', 'usd', 'dollar']):
            print(f"*** ID: {vid:>3} - {desc}")
        else:
            print(f"    ID: {vid:>3} - {desc}")
except Exception as e:
    print(f"Error: {e}")
