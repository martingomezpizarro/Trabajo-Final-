import sys, shutil, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# Source files
src1 = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\riesgos pais\embi_latam.csv'
src2 = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\riesgos pais\riesgo_pais_arg.csv'

# Find the data directory used by visualizador.html
# It's likely in the same folder or a subfolder
notebook_dir = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks'
data_dir = os.path.join(notebook_dir, 'data')

if not os.path.isdir(data_dir):
    print(f"data dir not found: {data_dir}")
    # List contents of notebook dir
    for item in os.listdir(notebook_dir):
        print(f"  {item}")
else:
    print(f"data dir exists: {data_dir}")
    # Check if files already exist
    dst1 = os.path.join(data_dir, 'embi_latam.csv')
    dst2 = os.path.join(data_dir, 'riesgo_pais_arg.csv')
    
    shutil.copy2(src1, dst1)
    shutil.copy2(src2, dst2)
    print(f"Copied embi_latam.csv -> {dst1}")
    print(f"Copied riesgo_pais_arg.csv -> {dst2}")
