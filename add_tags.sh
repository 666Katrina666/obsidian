#!/bin/bash

cd /workspace/Фанфики

# Файл 1: Midnight Loop - добавить теги
if [ -f "1. Midnight Loop - Gotham's 24 - Hour Reset.md" ]; then
    sed -i '1s/#dc #time_loop #artifact #hurt\/comfort/#dc #time_loop #artifact #hurt\/comfort #family_bonding #mystery #trust_issues/' "1. Midnight Loop - Gotham's 24 - Hour Reset.md"
    echo "Обновлен файл 1"
fi

# Файл 2: City of Doubt - добавить теги
if [ -f "2. City of Doubt - Nanotech Trust Plague.md" ]; then
    sed -i '1s/#dc #trust_issues #hurt\/comfort #nanotechnology/#dc #trust_issues #hurt\/comfort #nanotechnology #family_bonding #mystery/' "2. City of Doubt - Nanotech Trust Plague.md"
    echo "Обновлен файл 2"
fi

# Файл 3: Blood Oath - добавить теги
if [ -f "3. Blood Oath - De - aged and Bound.md" ]; then
    sed -i '1s/#dc #ABO #dark_Bruce #de-aging/#dc #ABO #dark_Bruce #de-aging #family_bonding #identity_crisis #parental_issues/' "3. Blood Oath - De - aged and Bound.md"
    echo "Обновлен файл 3"
fi

# Файл 4: Lazarus Redux - добавить теги
if [ -f "4. Lazarus Redux - Bruce's Synthetic Pit.md" ]; then
    sed -i '1s/#dc #dark_Bruce/#dc #dark_Bruce #family_bonding #parental_issues #experiments/' "4. Lazarus Redux - Bruce's Synthetic Pit.md"
    echo "Обновлен файл 4"
fi

# Файл 5: Bloodline Rewrite - добавить теги
if [ -f "5. Bloodline Rewrite - Heirs of Wayne.md" ]; then
    sed -i '1s/#dc/#dc #family_bonding #identity_crisis #experiments #drama/' "5. Bloodline Rewrite - Heirs of Wayne.md"
    echo "Обновлен файл 5"
fi

# Файл 6: Pack Oath - добавить теги
if [ -f "6. Pack Oath - The Hidden Pup Revealed.md" ]; then
    sed -i '1s/#dc #ABO/#dc #ABO #family_bonding #identity_crisis #revelation #hurt_comfort/' "6. Pack Oath - The Hidden Pup Revealed.md"
    echo "Обновлен файл 6"
fi

# Файл 7: Pack Instincts - добавить теги
if [ -f "7. Pack Instincts - Roles and Scent Theory.md" ]; then
    sed -i '1s/#dc #ABO/#dc #ABO #family_bonding #supernatural #worldbuilding/' "7. Pack Instincts - Roles and Scent Theory.md"
    echo "Обновлен файл 7"
fi

# Файл 8: Pack Wave - добавить теги
if [ -f "8. Pack Wave - Gotham Under the Spell.md" ]; then
    sed -i '1s/#dc #ABO/#dc #ABO #family_bonding #supernatural #magic #drama/' "8. Pack Wave - Gotham Under the Spell.md"
    echo "Обновлен файл 8"
fi

# Файл 9: Pain Circuit - добавить теги
if [ -f "9. Pain Circuit - Shared Hurt, Shared Fight.md" ]; then
    sed -i '1s/#dc/#dc #family_bonding #hurt_comfort #emotional_healing #drama/' "9. Pain Circuit - Shared Hurt, Shared Fight.md"
    echo "Обновлен файл 9"
fi

echo "Завершено добавление тегов к первым 9 файлам"