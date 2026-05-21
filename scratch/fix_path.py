with open('scratch/run_data.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace("sys.path.insert(0, str(Path('..').resolve()))", "sys.path.insert(0, '.')")
with open('scratch/run_data.py', 'w', encoding='utf-8') as f:
    f.write(code)
