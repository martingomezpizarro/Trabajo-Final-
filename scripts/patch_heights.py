"""
Fix: Make charts properly sized like analizador_emae.
- Main chart: 55vh (55% of viewport)
- Diff chart: 40vh (40% of viewport)
- Correlation: 350px
- Container scrolls to fit all
"""
import os

PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# Fix c2 CSS
old = '#c2{min-height:420px;flex-shrink:0}'
new = '#c2{height:55vh;min-height:350px;flex-shrink:0}'
if old in content:
    content = content.replace(old, new, 1); count += 1
    print("1. c2 = 55vh")

# Fix c3 CSS  
old = '#c3{min-height:320px;flex-shrink:0}'
new = '#c3{height:40vh;min-height:300px;flex-shrink:0}'
if old in content:
    content = content.replace(old, new, 1); count += 1
    print("2. c3 = 40vh")

# Fix c4 CSS
old = '#c4{display:none;flex-shrink:0;flex-direction:row;gap:8px;padding:8px;min-height:320px}'
new = '#c4{display:none;flex-shrink:0;flex-direction:row;gap:8px;padding:8px;height:350px;min-height:300px}'
if old in content:
    content = content.replace(old, new, 1); count += 1
    print("3. c4 = 350px")

# Update Plotly heights to match
content = content.replace("height:420", "height:undefined", 1)  # c2 fills its container
count += 1; print("4. c2 plotly height = undefined (auto)")

content = content.replace("height:320", "height:undefined", 1)  # c3 fills its container
count += 1; print("5. c3 plotly height = undefined (auto)")

# Make sure #cw scrollbar is styled
old_cw_scroll = '#cw{flex:1;display:none;flex-direction:column;min-height:0;overflow-y:auto;overflow-x:hidden}'
new_cw_scroll = '#cw{flex:1;display:none;flex-direction:column;min-height:0;overflow-y:auto;overflow-x:hidden}\n#cw::-webkit-scrollbar{width:4px}#cw::-webkit-scrollbar-thumb{background:#2a2a50;border-radius:3px}'
if old_cw_scroll in content:
    content = content.replace(old_cw_scroll, new_cw_scroll, 1); count += 1
    print("6. Styled scrollbar")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone! {count} changes applied")
