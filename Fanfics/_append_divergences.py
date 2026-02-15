# -*- coding: utf-8 -*-
import os

fanfics = r'c:\Obsidian\Fanfics'

# 200: append ## Расхождение 2 + 509 from line 63 (0-indexed 62) to end
path_509 = os.path.join(fanfics, "509. Kitten trapped by Gotham superheroes.md")
with open(path_509, 'r', encoding='utf-8') as f:
    lines_509 = f.readlines()
div2_509 = ''.join(lines_509[62:])  # from "напиши следующую длинную главу" inclusive

for f in os.listdir(fanfics):
    if f.startswith('200.') and f.endswith('.md'):
        path_200 = os.path.join(fanfics, f)
        with open(path_200, 'r', encoding='utf-8') as fp:
            content = fp.read()
        if '## Расхождение 2' in content:
            print('200 already has Расхождение 2, skip')
        else:
            content += '\n\n---\n\n## Расхождение 2\n\n' + div2_509
            with open(path_200, 'w', encoding='utf-8') as fp:
                fp.write(content)
            print('200: appended Расхождение 2 from 509')
        break

# 207: append ## Расхождение 2 + 701 from line 220 (0-indexed 219) to end
path_701 = os.path.join(fanfics, "701. Jason Todd transition to the world of magic.md")
with open(path_701, 'r', encoding='utf-8') as f:
    lines_701 = f.readlines()
div2_701 = ''.join(lines_701[219:])  # from "Напиши план глав из этой истории" (line 220)

for f in os.listdir(fanfics):
    if f.startswith('207.') and f.endswith('.md'):
        path_207 = os.path.join(fanfics, f)
        with open(path_207, 'r', encoding='utf-8') as fp:
            content = fp.read()
        if '## Расхождение 2' in content:
            print('207 already has Расхождение 2, skip')
        else:
            content += '\n\n---\n\n## Расхождение 2\n\n' + div2_701
            with open(path_207, 'w', encoding='utf-8') as fp:
                fp.write(content)
            print('207: appended Расхождение 2 from 701')
        break

print('Done.')
