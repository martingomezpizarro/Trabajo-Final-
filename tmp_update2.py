with open('notebooks/01_base_de_datos.ipynb', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '"    descargar_ambito,\\n"',
    '"    descargar_ambito,\\n",\n    "    descargar_argentinadatos,\\n"'
)
text = text.replace(
    '"        \'fuente\': \'ambito\',  # O la fuente que corresponda\\n"',
    '"        \'fuente\': \'argentinadatos\',\\n"'
)
text = text.replace(
    '"        \'ticker\': \'riesgo_pais_arg\',\\n"',
    '"        \'ticker\': \'riesgo_pais\',\\n"'
)
text = text.replace(
    '"        elif var[\'fuente\'] == \'ambito\':\\n",\n    "            df = descargar_ambito(var[\'ticker\'], FECHA_INICIO, FECHA_FIN)\\n"',
    '"        elif var[\'fuente\'] == \'ambito\':\\n",\n    "            df = descargar_ambito(var[\'ticker\'], FECHA_INICIO, FECHA_FIN)\\n",\n    "        elif var[\'fuente\'] == \'argentinadatos\':\\n",\n    "            df = descargar_argentinadatos(var[\'ticker\'], FECHA_INICIO, FECHA_FIN)\\n"'
)

with open('notebooks/01_base_de_datos.ipynb', 'w', encoding='utf-8') as f:
    f.write(text)

print("Text replaced!")
