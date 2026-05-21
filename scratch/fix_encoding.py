with open('scratch/run_data.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = "import sys, io\nsys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n" + code
with open('scratch/run_data.py', 'w', encoding='utf-8') as f:
    f.write(code)
