import os

file_path = os.path.join('notebooks', 'visualizador.html')

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Fix CSS widths for Plotly containers
html = html.replace(
    '#anl-chart{min-height:250px}', 
    '#anl-chart{min-height:250px;width:100%}'
)
html = html.replace(
    '#anl-corr>div{flex:1;min-height:0}', 
    '#anl-corr>div{flex:1;min-height:0;width:100%}'
)

# Fix JS switchTab to resize analysis charts
old_js1 = "setTimeout(()=>{if(t==='simulator'){['sc1','sc2','sc3'].forEach(id=>{const e=document.getElementById(id);if(e&&e.data)Plotly.Plots.resize(e)})}},50);"
new_js1 = "setTimeout(()=>{if(t==='simulator'){['sc1','sc2','sc3'].forEach(id=>{const e=document.getElementById(id);if(e&&e.data)Plotly.Plots.resize(e)})}if(t==='analysis'){['anl-chart','anl-acf','anl-pacf'].forEach(id=>{const e=document.getElementById(id);if(e&&e.data)Plotly.Plots.resize(e)})}},50);"
if old_js1 in html:
    html = html.replace(old_js1, new_js1)

# Add resize to runAnalysis just to be safe
old_js2 = "document.getElementById('adf-results').innerHTML='';"
new_js2 = "document.getElementById('adf-results').innerHTML='';setTimeout(()=>{['anl-chart','anl-acf','anl-pacf'].forEach(id=>{const e=document.getElementById(id);if(e&&e.data)Plotly.Plots.resize(e)})},50);"
if old_js2 in html:
    html = html.replace(old_js2, new_js2)

# Update global resize handler
old_js3 = "window.addEventListener('resize',()=>render());"
new_js3 = "window.addEventListener('resize',()=>{render();['sc1','sc2','sc3','anl-chart','anl-acf','anl-pacf'].forEach(id=>{const e=document.getElementById(id);if(e&&e.data)Plotly.Plots.resize(e)})});"
if old_js3 in html:
    html = html.replace(old_js3, new_js3)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Patch applied successfully!")
