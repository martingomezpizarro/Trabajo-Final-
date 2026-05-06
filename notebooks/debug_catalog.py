import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

filepath = 'visualizador.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

grp_start = "{ grp:'PBI y Cuentas Nacionales', clr:'#ec4899', subs:["
idx = content.find(grp_start)
print(f'Group at index {idx}')
snippet = content[idx:idx+800]
print(repr(snippet))
