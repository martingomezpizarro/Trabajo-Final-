"""Make the main comparison chart (c2) take most of the screen like analizador_emae."""
import os
PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')
with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# c2: main chart -> 80vh (fills nearly full screen, rest scrolls below)
content = content.replace(
    '#c2{height:55vh;min-height:350px;flex-shrink:0}',
    '#c2{height:80vh;min-height:500px;flex-shrink:0}', 1)
print("c2 = 80vh")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
