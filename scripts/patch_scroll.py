"""
Patch: Make comparison charts bigger with scroll support.
- #cw becomes scrollable (overflow-y: auto)
- Each chart gets fixed min-height instead of flex ratios
- Difference chart (c3) gets much bigger
"""
import os

PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# 1. Make #cw scrollable with fixed children heights instead of flex
# Current: #cw{flex:1;display:none;flex-direction:column;min-height:0}
old_cw = '#cw{flex:1;display:none;flex-direction:column;min-height:0}'
new_cw = '#cw{flex:1;display:none;flex-direction:column;min-height:0;overflow-y:auto;overflow-x:hidden}'
if old_cw in content:
    content = content.replace(old_cw, new_cw, 1)
    count += 1
    print("1. Made #cw scrollable")
else:
    print("MISS: #cw rule not found, searching...")
    # Try to find it
    idx = content.find('#cw{')
    if idx > 0:
        end = content.find('}', idx)
        old = content[idx:end+1]
        print(f"   Found: {old}")
        if 'overflow' not in old:
            new = old[:-1] + ';overflow-y:auto;overflow-x:hidden}'
            content = content.replace(old, new, 1)
            count += 1
            print("   Fixed with overflow")

# 2. Make c2 (main chart) a fixed height
old_c2 = '#c2{flex:3;min-height:0}'
new_c2 = '#c2{min-height:420px;flex-shrink:0}'
if old_c2 in content:
    content = content.replace(old_c2, new_c2, 1)
    count += 1
    print("2. c2 fixed height 420px")
else:
    print("MISS: #c2 rule")

# 3. Make c3 (diff chart) much bigger 
old_c3 = '#c3{flex:2;min-height:0}'
new_c3 = '#c3{min-height:320px;flex-shrink:0}'
if old_c3 in content:
    content = content.replace(old_c3, new_c3, 1)
    count += 1
    print("3. c3 fixed height 320px")
else:
    print("MISS: #c3 rule")

# 4. Make c4 (correlation) taller
old_c4 = '#c4{display:none;flex-shrink:0;flex-direction:row;gap:8px;padding:8px;height:280px}'
new_c4 = '#c4{display:none;flex-shrink:0;flex-direction:row;gap:8px;padding:8px;min-height:320px}'
if old_c4 in content:
    content = content.replace(old_c4, new_c4, 1)
    count += 1
    print("4. c4 min-height 320px")
else:
    print("MISS: #c4 rule")

# 5. Update rCmp heights in JS - use fixed pixel heights instead of percentages
# The JS calculates heights as percentages of #cw clientHeight. 
# With scroll, we should use fixed values instead.
old_h_calc = "const hT=document.getElementById('cw').clientHeight||500;"
new_h_calc = "const hT=900; // fixed total height for scrollable layout"
if old_h_calc in content:
    content = content.replace(old_h_calc, new_h_calc, 1)
    count += 1
    print("5. Fixed chart height calculation")
else:
    print("MISS: hT calculation")

# 6. Update the height ratios in Plotly.react calls
# c2: was .45 of hT -> make it 420
old_c2_h = "height:Math.round(hT*.45)"
new_c2_h = "height:420"
if old_c2_h in content:
    content = content.replace(old_c2_h, new_c2_h, 1)
    count += 1
    print("6. c2 plotly height = 420")

# c3: was .25 of hT -> make it 320
old_c3_h = "height:Math.round(hT*.25)"
new_c3_h = "height:320"
if old_c3_h in content:
    content = content.replace(old_c3_h, new_c3_h, 1)
    count += 1
    print("7. c3 plotly height = 320")

# correlation scatter/heatmap height
old_corr_h1 = "height:260"
new_corr_h1 = "height:300"
content = content.replace(old_corr_h1, new_corr_h1)
count += 1
print("8. Correlation chart heights = 300")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone! Applied {count} changes")
