"""
Patch visualizador.html:
1. CSS: Update palette to analizador_emae style, remove duplicates, add new styles
2. HTML: Add comparison controls (bar/line toggle) and correlation panel
3. JS: Add correlation matrix, bar/area diff charts, scatter plot
"""
import re, sys, os

PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# ══════════════════════════════════════════
# 1. CSS REPLACEMENTS
# ══════════════════════════════════════════

css_replacements = [
    # Sidebar
    ('#sb{width:310px;min-width:210px;background:#10102a;border-right:1px solid #222244;display:flex;flex-direction:column;overflow:hidden}',
     '#sb{width:285px;min-width:180px;background:#10102a;border-right:1px solid #1e1e42;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0}'),
    ('#sb-head{padding:12px 14px;background:#14143a;border-bottom:1px solid #222244}',
     '#sb-head{padding:11px 13px 8px;background:#14143a;border-bottom:1px solid #1e1e42}'),
    ('#sb-head h1{font-size:12px;', '#sb-head h1{font-size:11px;'),
    ('#sb-head small{color:#555;font-size:10px}',
     '#sb-head small{color:#3a3a5a;font-size:9px}'),
    ('#search{margin:8px;padding:6px 10px;background:#181838;border:1px solid #2a2a50;border-radius:5px;color:#d4d4e8;font-size:12px;font-family:inherit;width:calc(100% - 16px)}',
     '#search{margin:6px 7px;padding:4px 8px;background:#181838;border:1px solid #252550;border-radius:4px;color:#d4d4e8;font-size:11px;font-family:inherit;width:calc(100% - 14px)}'),
    # Tree items
    ('.grp-label{padding:7px 12px;font-size:10px;font-weight:700;color:#555;',
     '.grp-label{padding:7px 10px 4px;font-size:9.5px;font-weight:700;color:#404080;'),
    ('.item{padding:4px 12px 4px 16px;font-size:11.5px;cursor:pointer;border-left:3px solid transparent;display:flex;align-items:center;gap:5px;color:#888;transition:all .12s}',
     '.item{padding:3px 10px 3px 22px;font-size:11px;cursor:pointer;border-left:2px solid transparent;display:flex;align-items:center;gap:6px;color:#5a5a98;transition:all .1s}'),
    # Bar
    ('#bar{background:#12122e;border-bottom:1px solid #222244;padding:8px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}',
     '#bar{background:#12122e;border-bottom:1px solid #1e1e42;padding:6px 12px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;flex-shrink:0;min-height:40px}'),
    ('#title{font-size:14px;font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
     '#title{font-size:12px;font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#cccce8;min-width:100px}'),
    # Buttons
    ('.mbtn{padding:4px 12px;font-size:11px;border:1px solid #333;border-radius:4px;background:#161636;color:#999;cursor:pointer;font-family:inherit;transition:all .12s}',
     '.mbtn{padding:3px 10px;font-size:10.5px;border:1px solid #252545;border-radius:3px;background:#161636;color:#777;cursor:pointer;font-family:inherit;transition:all .1s;white-space:nowrap}'),
    ('.dbtn{padding:4px 10px;font-size:10px;border:1px solid #333;border-radius:4px;background:#161636;color:#888;cursor:pointer;font-family:inherit;transition:all .12s}',
     '.dbtn{padding:3px 9px;font-size:10px;border:1px solid #252545;border-radius:3px;background:#161636;color:#777;cursor:pointer;font-family:inherit;transition:all .1s;white-space:nowrap}'),
    ('.dbtn.on{background:#d97706;border-color:#d97706;color:#fff;font-weight:600}',
     '.dbtn.on{background:#92400e;border-color:#f59e0b;color:#fcd34d;font-weight:600}'),
    ('.dbtn.disabled{opacity:.3;', '.dbtn.disabled{opacity:.25;'),
    ('.sep{width:1px;height:20px;background:#2a2a4a}',
     '.sep{width:1px;height:16px;background:#1e1e42;flex-shrink:0}'),
    # Info bar
    ('#info{padding:4px 16px;background:#0e0e22;font-size:10px;color:#444;border-bottom:1px solid #181838;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
     '#info{background:#0e0e26;border-bottom:1px solid #151530;padding:3px 12px;min-height:24px;display:flex;align-items:center;gap:12px;overflow-x:auto;flex-shrink:0;font-size:10px;color:#33335a}'),
]

for old, new in css_replacements:
    if old in content:
        content = content.replace(old, new, 1)
        print(f"  CSS: replaced '{old[:40]}...'")
    else:
        print(f"  CSS MISS: '{old[:50]}...'")

# Remove duplicate CSS block (first occurrence of /* === MAIN TABS === */ through the first .anl-stat .lbl line)
# The duplicate is between the first /* === MAIN TABS === */ and the second one
first_main_tabs = content.find('/* === MAIN TABS === */')
if first_main_tabs > 0:
    second_main_tabs = content.find('/* === MAIN TABS === */', first_main_tabs + 10)
    if second_main_tabs > 0:
        content = content[:first_main_tabs] + '\n' + content[second_main_tabs:]
        print("  CSS: removed duplicate block")

# Add new CSS before </style>
new_css = """
/* === COMPARISON CONTROLS === */
#vbar-cmp{background:#0d0d20;border-top:1px solid #151530;border-bottom:1px solid #151530;padding:4px 12px;display:flex;align-items:center;gap:6px;flex-shrink:0;display:none}
.vbtn2{padding:3px 9px;font-size:10px;border:1px solid #252545;border-radius:3px;background:#161636;color:#777;cursor:pointer;font-family:inherit;transition:all .1s;white-space:nowrap}
.vbtn2:hover{border-color:#f59e0b;color:#fcd34d}
.vbtn2.on{background:#92400e;border-color:#f59e0b;color:#fcd34d;font-weight:600}
.malabel{font-size:9px;color:#404060;text-transform:uppercase;letter-spacing:.06em;flex-shrink:0}
/* === CORRELATION === */
#c4{display:none;flex-shrink:0;flex-direction:row;gap:8px;padding:8px;height:280px}
#corr-ctrl{display:flex;flex-direction:column;gap:5px;min-width:170px;padding:8px 10px;background:#10102a;border:1px solid #1e1e42;border-radius:6px;font-size:10px}
#corr-ctrl label{font-size:9px;color:#555;text-transform:uppercase}
#corr-ctrl input{padding:3px 6px;background:#181838;border:1px solid #2a2a50;border-radius:3px;color:#d4d4e8;font-size:10px;font-family:inherit;color-scheme:dark}
#corr-ctrl input:focus{outline:none;border-color:#7c3aed}
#corr-scatter{flex:1;min-height:0}
.corr-badge{text-align:center;padding:4px;background:#14143a;border:1px solid #222244;border-radius:4px;margin-top:3px}
.corr-badge .val{font-size:14px;font-weight:700;color:#e0d4ff}
.corr-badge .lbl{font-size:8px;color:#666;text-transform:uppercase}
.pos{color:#22c55e}.neg{color:#ef4444}
"""
content = content.replace('</style>', new_css + '</style>', 1)
print("  CSS: added new styles")

# ══════════════════════════════════════════
# 2. HTML CHANGES
# ══════════════════════════════════════════

# Replace the comparison wrapper to add vbar-cmp and c4
old_cw = '<div id="cw"><div id="c2"></div><div id="c3"></div></div>'
new_cw = '''<div id="cw">
    <div id="c2"></div>
    <div id="vbar-cmp">
     <span class="malabel">Diferencia:</span>
     <button class="vbtn2 on" id="vDiffBar" onclick="setDiffChartType('bar')">Barras</button>
     <button class="vbtn2" id="vDiffLin" onclick="setDiffChartType('line')">L\u00ednea + \u00c1rea</button>
    </div>
    <div id="c3"></div>
    <div id="c4">
     <div id="corr-ctrl">
      <label style="color:#a78bfa;font-weight:700;font-size:10px">\u26a1 Correlaci\u00f3n</label>
      <label>Desde:</label><input type="date" id="corr-from">
      <label>Hasta:</label><input type="date" id="corr-to">
      <button class="vbtn2 on" onclick="updateCorrelation()" style="margin-top:4px">\u25b6 Calcular</button>
      <div id="corr-badges"></div>
     </div>
     <div id="corr-scatter"></div>
    </div>
   </div>'''
if old_cw in content:
    content = content.replace(old_cw, new_cw, 1)
    print("  HTML: replaced #cw section")
else:
    print("  HTML MISS: #cw section not found")

# ══════════════════════════════════════════
# 3. JS CHANGES
# ══════════════════════════════════════════

# 3a. Add new state variable after existing state
old_state = "let cur=null, mode='ind', diffOn=false, logOn=true, deflMode=null;"
new_state = "let cur=null, mode='ind', diffOn=false, logOn=true, deflMode=null, diffChartType='bar';"
content = content.replace(old_state, new_state, 1)
print("  JS: added diffChartType state")

# 3b. Rename first diff() to diffSimple() to avoid collision with simulator's diff()
old_diff_fn = "function diff(v){ return v.map((x,i)=>i===0?null:(x!=null&&v[i-1]!=null?x-v[i-1]:null)) }"
new_diff_fn = "function diffSimple(v){ return v.map((x,i)=>i===0?null:(x!=null&&v[i-1]!=null?x-v[i-1]:null)) }"
content = content.replace(old_diff_fn, new_diff_fn, 1)
print("  JS: renamed diff() to diffSimple()")

# Update references to diffSimple in transform()
content = content.replace("if(diffOn) v=diff(v);", "if(diffOn) v=diffSimple(v);", 1)
print("  JS: updated transform() reference")

# 3c. Add new toggle function and correlation functions before rCmp
new_js_functions = r"""
// ═══════════════════════════════════════
// DIFF CHART TYPE TOGGLE
// ═══════════════════════════════════════
function setDiffChartType(t){
  diffChartType=t;
  document.getElementById('vDiffBar').classList.toggle('on',t==='bar');
  document.getElementById('vDiffLin').classList.toggle('on',t==='line');
  if(mode==='cmp') rCmp();
}

// ═══════════════════════════════════════
// CORRELATION HELPERS
// ═══════════════════════════════════════
function pearsonCorr(a,b){
  const n=a.length;if(n<3)return NaN;
  const ma=a.reduce((s,x)=>s+x,0)/n, mb=b.reduce((s,x)=>s+x,0)/n;
  let num=0,da=0,db=0;
  for(let i=0;i<n;i++){const xa=a[i]-ma,xb=b[i]-mb;num+=xa*xb;da+=xa*xa;db+=xb*xb}
  const den=Math.sqrt(da*db);
  return den===0?0:num/den;
}

function getAlignedPairs(idA,idB,from,to){
  const eA=D[idA],eB=D[idB];if(!eA||!eB)return null;
  const shouldDeflA=ds.has(idA),shouldDeflB=ds.has(idB);
  const vA=transform(eA.fechas,eA.valores,shouldDeflA);
  const vB=transform(eB.fechas,eB.valores,shouldDeflB);
  const mapB={};eB.fechas.forEach((d,i)=>{if(vB[i]!=null)mapB[d]=vB[i]});
  const pA=[],pB=[],dates=[];
  eA.fechas.forEach((d,i)=>{
    if(from&&d<from)return;if(to&&d>to)return;
    if(vA[i]!=null&&mapB[d]!=null){pA.push(vA[i]);pB.push(mapB[d]);dates.push(d)}
  });
  return pA.length<3?null:{a:pA,b:pB,dates};
}

function updateCorrelation(){
  const ids=[...cs];if(ids.length<2)return;
  const from=document.getElementById('corr-from').value||null;
  const to=document.getElementById('corr-to').value||null;

  // Build correlation matrix
  const n=ids.length;
  const matrix=Array.from({length:n},()=>new Float64Array(n));
  const labels=ids.map(id=>D[id]?.meta.nombre||id);
  for(let i=0;i<n;i++){
    matrix[i][i]=1;
    for(let j=i+1;j<n;j++){
      const p=getAlignedPairs(ids[i],ids[j],from,to);
      const r=p?pearsonCorr(p.a,p.b):NaN;
      matrix[i][j]=r;matrix[j][i]=r;
    }
  }

  // Badges
  const bb=document.getElementById('corr-badges');bb.innerHTML='';
  if(n===2){
    const r=matrix[0][1];
    bb.innerHTML=`<div class="corr-badge"><div class="val ${r>=0?'pos':'neg'}">${isNaN(r)?'—':r.toFixed(4)}</div><div class="lbl">Pearson ρ</div></div>`;
  } else {
    for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
      const r=matrix[i][j];
      bb.innerHTML+=`<div class="corr-badge" style="margin-bottom:2px"><div class="val ${r>=0?'pos':'neg'}" style="font-size:11px">${isNaN(r)?'—':r.toFixed(3)}</div><div class="lbl">${labels[i].slice(0,8)} × ${labels[j].slice(0,8)}</div></div>`;
    }
  }

  // Heatmap for matrix
  if(n>=3){
    const z=matrix.map(r=>Array.from(r));
    const ann=[];
    for(let i=0;i<n;i++)for(let j=0;j<n;j++){
      ann.push({x:j,y:i,text:isNaN(z[i][j])?'—':z[i][j].toFixed(2),showarrow:false,font:{color:Math.abs(z[i][j])>0.5?'#fff':'#888',size:10}});
    }
    Plotly.react('corr-scatter',[{z,x:labels,y:labels,type:'heatmap',colorscale:[[0,'#ef4444'],[0.5,'#0b0b18'],[1,'#22c55e']],zmin:-1,zmax:1,showscale:true,colorbar:{thickness:10,tickfont:{size:8,color:'#888'}}}],{
      ...LB,margin:{l:80,r:20,t:10,b:80},annotations:ann,
      xaxis:{tickangle:45,tickfont:{size:8}},yaxis:{tickfont:{size:8},autorange:'reversed'},
      height:260
    },{responsive:true,displayModeBar:false});
  } else {
    // Scatter for 2 series
    const p=getAlignedPairs(ids[0],ids[1],from,to);
    if(!p){Plotly.purge('corr-scatter');return}
    // Regression line
    const ma=p.a.reduce((s,x)=>s+x,0)/p.a.length,mb=p.b.reduce((s,x)=>s+x,0)/p.b.length;
    let num=0,den=0;for(let i=0;i<p.a.length;i++){num+=(p.a[i]-ma)*(p.b[i]-mb);den+=(p.a[i]-ma)*(p.a[i]-ma)}
    const slope=den?num/den:0,intercept=mb-slope*ma;
    const xmin=Math.min(...p.a),xmax=Math.max(...p.a);
    Plotly.react('corr-scatter',[
      {x:p.a,y:p.b,type:'scatter',mode:'markers',marker:{color:'#7c3aed',size:4,opacity:.6},
       hovertemplate:'%{x:.2f} | %{y:.2f}<extra></extra>',name:'Obs'},
      {x:[xmin,xmax],y:[intercept+slope*xmin,intercept+slope*xmax],type:'scatter',mode:'lines',
       line:{color:'#f59e0b',width:1.5,dash:'dash'},name:'Reg',hoverinfo:'skip'}
    ],{...LB,margin:{l:50,r:10,t:10,b:40},
      xaxis:{title:{text:labels[0],font:{size:9}},gridcolor:GC},
      yaxis:{title:{text:labels[1],font:{size:9}},gridcolor:GC},
      showlegend:false,height:260
    },{responsive:true,displayModeBar:false});
  }
}

"""

# Insert before rCmp function
insert_marker = "// ═══════════════════════════════════════\n// RENDER COMPARACIÓN"
if insert_marker in content:
    content = content.replace(insert_marker, new_js_functions + insert_marker, 1)
    print("  JS: added correlation + toggle functions")
else:
    # Try with \r\n
    insert_marker2 = "// ═══════════════════════════════════════\r\n// RENDER COMPARACIÓN"
    if insert_marker2 in content:
        content = content.replace(insert_marker2, new_js_functions + insert_marker2, 1)
        print("  JS: added correlation + toggle functions")
    else:
        print("  JS MISS: insert marker for new functions not found")

# 3d. Replace the rCmp function with enhanced version
old_rCmp_start = "function rCmp(){\r\n document.getElementById('c1').style.display='none';"
old_rCmp_end = "  // ── Sync ejes ──\r\n  setupSync();\r\n}"

# Find the full rCmp function
rCmp_start = content.find("function rCmp(){")
rCmp_end = content.find("function setupSync(){")
if rCmp_start > 0 and rCmp_end > 0:
    new_rCmp = r"""function rCmp(){
 document.getElementById('c1').style.display='none';
 const ids=[...cs];
 if(ids.length<2){
   document.getElementById('cw').style.display='none';
   document.getElementById('empty').style.display='flex';
   document.getElementById('vbar-cmp').style.display='none';
   document.getElementById('c4').style.display='none';
   return;
 }
 document.getElementById('cw').style.display='flex';
 document.getElementById('empty').style.display='none';
 document.getElementById('vbar-cmp').style.display='flex';
 document.getElementById('c4').style.display='flex';

 document.getElementById('title').textContent='Comparación — '+ids.length+' series';
 document.getElementById('info').textContent=ids.map(id=>{
   const n=D[id]?.meta.nombre||id;
   return ds.has(id)&&deflMode ? n+(deflMode==='cer'?' /CER':' /IPC') : n;
 }).join(' | ');

 // ── Fecha inicio más tardía para base 100 ──
 let latestStart=null;
 ids.forEach(id=>{
   const e=D[id]; if(!e) return;
   const f=e.fechas[0];
   if(!latestStart||f>latestStart) latestStart=f;
 });

 // ── Traces ──
 const tc=[], td=[];
 let refV=null, refD=null;

 ids.forEach((id,i)=>{
  const e=D[id]; if(!e) return;
  const m=e.meta, c=COL[i%COL.length];
  const shouldDefl=ds.has(id);
  const tl=transformLabel(shouldDefl);

  const raw=transform(e.fechas, e.valores, shouldDefl);

  // Base idx: primer dato >= latestStart
  let baseIdx=0;
  for(let j=0;j<e.fechas.length;j++){
    if(e.fechas[j]>=latestStart && raw[j]!=null){baseIdx=j;break;}
  }
  const v100=b100from(raw, baseIdx);
  const label=m.nombre+(shouldDefl&&deflMode?tl:'');

  tc.push({
    x:e.fechas, y:v100, type:'scatter', mode:'lines',
    name:label, line:{color:c,width:2},
    hovertemplate:`<b>${label}</b><br>%{x}<br>Base 100: %{y:.2f}<extra></extra>`
  });

  if(i===0){ refV=v100; refD=e.fechas; }
  else {
    const rm={}; refD?.forEach((d,j)=>rm[d]=refV[j]);
    const df=e.fechas.map((d,j)=>{
      const rv=rm[d];
      return (v100[j]!=null&&rv!=null)?v100[j]-rv:null;
    });
    td.push({id,label:m.nombre,fechas:e.fechas,diff:df,color:c});
  }
 });

 const hT=document.getElementById('cw').clientHeight||500;
 const baseLbl=latestStart?`Base 100 al ${latestStart}`:'Base 100';

 // Gráfico superior: con rangeselector
 Plotly.react('c2',tc,{
  ...LB, height:Math.round(hT*.45), margin:{l:60,r:20,t:40,b:15},
  yaxis:{type:logOn?'log':'linear',title:baseLbl+(logOn?' (log)':''),color:FC,gridcolor:GC},
  xaxis:{type:'date',color:FC,gridcolor:GC,
    rangeselector:RSEL
  },
  title:{text:'Evolución comparada — '+baseLbl,font:{size:12}},
  legend:{bgcolor:'#10102a',orientation:'h',y:1.1}
 },{displayModeBar:false,responsive:true});

 // Gráfico inferior: diferencia con barras o línea+área
 const diffTraces=[];
 if(diffChartType==='bar'){
   td.forEach(s=>{
     const colors=s.diff.map(v=>v==null?'rgba(0,0,0,0)':v>=0?'rgba(34,197,94,0.7)':'rgba(239,68,68,0.7)');
     diffTraces.push({
       x:s.fechas, y:s.diff, type:'bar', name:`${s.label} − ref`,
       marker:{color:colors},
       hovertemplate:`%{x}<br>Dif: %{y:.2f}<extra></extra>`
     });
   });
 } else {
   // Line + shaded area
   td.forEach(s=>{
     const yPos=s.diff.map(v=>v!=null&&v>=0?v:0);
     const yNeg=s.diff.map(v=>v!=null&&v<0?v:0);
     diffTraces.push({
       x:s.fechas, y:s.diff, type:'scatter', mode:'lines',
       name:`${s.label} − ref`, line:{color:s.color,width:1.5},
       hovertemplate:`%{x}<br>Dif: %{y:.2f}<extra></extra>`
     });
     diffTraces.push({
       x:s.fechas, y:yPos, type:'scatter', mode:'none',
       fill:'tozeroy', fillcolor:'rgba(34,197,94,0.15)',
       showlegend:false, hoverinfo:'skip'
     });
     diffTraces.push({
       x:s.fechas, y:yNeg, type:'scatter', mode:'none',
       fill:'tozeroy', fillcolor:'rgba(239,68,68,0.15)',
       showlegend:false, hoverinfo:'skip'
     });
   });
 }
 // Zero line
 diffTraces.push({x:refD,y:refD?.map(()=>0),type:'scatter',mode:'lines',
  line:{color:'#333',dash:'dot',width:1},showlegend:false,hoverinfo:'skip'});

 Plotly.react('c3',diffTraces,{
  ...LB, height:Math.round(hT*.25), margin:{l:60,r:20,t:8,b:50},
  yaxis:{title:'Diferencia (pts base 100)',color:FC,gridcolor:GC},
  xaxis:{type:'date',color:FC,gridcolor:GC,
    rangeslider:{visible:true,bgcolor:'#10102a',bordercolor:'#222244'}
  },
  barmode:'group',
  showlegend:true,
  legend:{bgcolor:'#10102a',orientation:'h',y:-.25}
 },{displayModeBar:false,responsive:true});

 // Auto-calculate correlation
 updateCorrelation();

 // ── Sync ejes ──
 setupSync();
}

"""
    content = content[:rCmp_start] + new_rCmp + content[rCmp_end:]
    print("  JS: replaced rCmp() function")
else:
    print("  JS MISS: rCmp function boundaries not found")

# 3e. Add resize for new charts
old_resize = "['sc1','sc2','sc3','anl-chart','anl-acf','anl-pacf'].forEach"
new_resize = "['sc1','sc2','sc3','anl-chart','anl-acf','anl-pacf','corr-scatter'].forEach"
content = content.replace(old_resize, new_resize)
print("  JS: updated resize handlers")

# ══════════════════════════════════════════
# WRITE
# ══════════════════════════════════════════
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Done! {original_len} → {len(content)} bytes")
