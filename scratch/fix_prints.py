import json
import glob

for nb_path in ['notebooks/02a_analisis_basico.ipynb', 'notebooks/02b_analisis_completo.ipynb']:
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except FileNotFoundError:
        continue
        
    modified = False
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            source = c.get('source', [])
            if not source: continue
            
            new_source = []
            i = 0
            while i < len(source):
                line = source[i]
                # Check for "print(f'\n" or "print('\n" at the start (ignoring leading spaces)
                stripped = line.lstrip()
                if stripped == "print(f'\n" or stripped == "print('\n":
                    # We remove the trailing newline and add \n inside the string
                    spaces = line[:len(line) - len(stripped)]
                    is_fstring = "f" in stripped
                    prefix = f"{spaces}print(f'\\n" if is_fstring else f"{spaces}print('\\n"
                    
                    if i + 1 < len(source):
                        # Merge with the next line
                        new_source.append(prefix + source[i+1])
                        i += 1
                        modified = True
                    else:
                        new_source.append(line)
                elif "print(f'\n" in line or "print('\n" in line:
                    # In case it's in the middle of a line
                    if line.endswith("\n"):
                        new_line = line.replace("print(f'\n", "print(f'\\n").replace("print('\n", "print('\\n")
                        if new_line != line and not new_line.endswith('\n'):
                            if i + 1 < len(source):
                                new_source.append(new_line + source[i+1])
                                i += 1
                                modified = True
                            else:
                                new_source.append(line)
                        else:
                            new_source.append(new_line)
                    else:
                        new_source.append(line)
                else:
                    new_source.append(line)
                i += 1
            c['source'] = new_source

    if modified:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"Fixed {nb_path}")
    else:
        print(f"No changes for {nb_path}")
