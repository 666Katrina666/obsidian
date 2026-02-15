# -*- coding: utf-8 -*-
import os

fanfics = r'c:\Obsidian\Fanfics'
base = open(os.path.join(fanfics, '_179_base.txt'), 'r', encoding='utf-8').readlines()[:157]
base = ''.join(base)

with open(os.path.join(fanfics, "352. Spark's Secret - Red Hood's Magical Masquerade.md"), 'r', encoding='utf-8') as f:
    g352 = f.readlines()

# 352: line 52 = index 51 is "## Глава 1 - Неожиданное возвращение Искры", line 164 = index 163 is "## Глава 2 - Непрошеное превращение"
ch1_block = ''.join(g352[51:163])
div1_block = ''.join(g352[163:])

with open(os.path.join(fanfics, "450. Jason Todd returns to his place.md"), 'r', encoding='utf-8') as f:
    a450 = f.readlines()
div2_block = ''.join(a450[152:])

out = base
out += '\n' + ch1_block
out += '\n---\n\n## Расхождение 1\n\n' + div1_block
out += '\n---\n\n## Расхождение 2\n\n' + div2_block

for f in os.listdir(fanfics):
    if f.startswith('179'):
        path = os.path.join(fanfics, f)
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(out)
        print('Written', path)
        break
