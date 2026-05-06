"""
Patch CSS for visualizador.html (fix line ending issues from first run)
"""
import os

PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)
count = 0

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
        count += 1
    else:
        # Try stripping and searching
        pass

# Remove duplicate CSS block
first_mt = content.find('/* === MAIN TABS === */')
if first_mt > 0:
    second_mt = content.find('/* === MAIN TABS === */', first_mt + 10)
    if second_mt > 0 and (second_mt - first_mt) < 5000:
        content = content[:first_mt] + content[second_mt:]
        count += 1
        print(f"Removed duplicate CSS block")

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Applied {count} CSS replacements. {original_len} -> {len(content)} bytes")
