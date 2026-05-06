import sys

filepath = 'visualizador.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Build the strings to find/replace avoiding any shell interpolation issues
grp_start = "{ grp:'PBI y Cuentas Nacionales', clr:'#ec4899', subs:["

# Sub 1: En dólares (MEP)
sub1_start = "    { sub:'En d\u00f3lares (MEP)', items:["
sub1_end   = "    ]},"

# Sub 2: En pesos corrientes
sub2_start = "    { sub:'En pesos corrientes', items:["
sub2_end   = "    ]},"

# Find position of grp_start
idx = content.find(grp_start)
if idx == -1:
    print('ERROR: group start not found')
    sys.exit(1)

print(f'Found group at index {idx}')

# Find sub1 after idx
s1 = content.find(sub1_start, idx)
if s1 == -1:
    print('ERROR: sub1 not found')
    sys.exit(1)
print(f'Found sub1 at index {s1}')

# Find end of sub2
# sub2 ends after sub2_end (i.e., closing ]},)
s2_start = content.find(sub2_start, s1)
if s2_start == -1:
    print('ERROR: sub2 not found')
    sys.exit(1)
print(f'Found sub2 at index {s2_start}')

# Find the closing ']}, \n' of sub2
# We look for ']},\r\n' or ']},\n' after sub2_start
end_marker1 = "    ]},\r\n    { sub:'Oferta"
end_marker2 = "    ]},\n    { sub:'Oferta"

e1 = content.find(end_marker1, s2_start)
e2 = content.find(end_marker2, s2_start)
e = e1 if e1 != -1 else e2
if e == -1:
    print('ERROR: end of sub2 not found')
    # print snippet
    print(repr(content[s2_start:s2_start+400]))
    sys.exit(1)

# We want to remove from s1 (start of sub1) to end of sub2's ]},\r\n
# That is: content[s1 : e + len("    ]},\r\n")]
if e1 != -1:
    cut_end = e + len("    ]},\r\n")
else:
    cut_end = e + len("    ]},\n")

removed = content[s1:cut_end]
print(f'Will remove {len(removed)} chars:')
print(repr(removed[:200]))

content_new = content[:s1] + content[cut_end:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content_new)

print('OK: file written successfully')
