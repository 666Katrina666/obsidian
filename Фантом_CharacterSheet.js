// Character data
let character = {
    name: "Фантом",
    evolution: 0,
    azur: { current: 40, max: 60 },
    neurosferas: 1,
    health: {
        head: 4, body: 7, rightarm: 6, leftarm: 6,
        rightleg: 6, leftleg: 6, anima: 8
    },
    armor: {
        head: 6, body: 22, rightarm: 6, leftarm: 6,
        rightleg: 6, leftleg: 6
    },
    endurance: { current: 12, max: 12 },
    durability: { current: 30, max: 30 },
    weapons: {
        shotgun: {
            magazine: 2,
            regularAmmo: 10,
            incendiaryAmmo: 6,
            ammoType: "regular"
        },
        sword: {
            activationsUsed: 0,
            activated: false,
            roundsLeft: 0
        }
    },
    actions: [false, false, false],
    round: 1,
    notes: "",
    equipment: "✓ Дробовик \"Зажигалочка\"\n✓ Меч \"Легион\"\n✓ Броня \"Гардиан\"\n✓ Термическая граната\n✓ Переносное Хранилище",
    armorEquipped: true
};

// Update stats display
function updateStats() {
    const evolution = parseInt(document.getElementById('evolution').value) || 0;
    character.evolution = evolution;
    
    // Update resistance
    document.getElementById('resistance').textContent = 2;
    
    // Update source
    document.getElementById('source').textContent = 3;
    
    // Update defense (base 4 + improvements)
    const defenseBase = 4;
    const defenseBonus = 1; // From source improvement
    const defenseTotal = defenseBase + defenseBonus;
    document.getElementById('defense').textContent = defenseTotal;
    // Update defense tooltip
    const defenseContainer = document.getElementById('defense').closest('.tooltip-container');
    if (defenseContainer) {
        const defenseTooltip = defenseContainer.querySelector('.tooltip-text');
        if (defenseTooltip) {
            defenseTooltip.textContent = `${defenseBase} базовая + ${defenseBonus} источник = ${defenseTotal}`;
        }
    }
    
    // Update speed (base 25 + improvements)
    const speedBase = 25;
    const speedBonus = 5; // From source improvement
    const speedTotal = speedBase + speedBonus;
    document.getElementById('speed').textContent = speedTotal;
    document.getElementById('speed-display').textContent = speedTotal;
    // Update speed tooltip
    const speedContainer = document.getElementById('speed').closest('.tooltip-container');
    if (speedContainer) {
        const speedTooltip = speedContainer.querySelector('.tooltip-text');
        if (speedTooltip) {
            speedTooltip.textContent = `${speedBase} базовая + ${speedBonus} источник = ${speedTotal} фт`;
        }
    }
    
    // Update stealth (base 0 + improvements)
    const stealthBase = 0;
    const stealthBonus = 1; // From source improvement
    const stealthTotal = stealthBase + stealthBonus;
    document.getElementById('stealth').textContent = stealthTotal;
    // Update stealth tooltip
    const stealthContainer = document.getElementById('stealth').closest('.tooltip-container');
    if (stealthContainer) {
        const stealthTooltip = stealthContainer.querySelector('.tooltip-text');
        if (stealthTooltip) {
            stealthTooltip.textContent = `${stealthBase} базовая + ${stealthBonus} источник = ${stealthTotal}`;
        }
    }
    
    // Update endurance (calculated from lost health)
    calculateEndurance();
    document.getElementById('endurance-max').textContent = character.endurance.max || 12;
    
    // Update durability (calculated from lost armor)
    calculateDurability();
    document.getElementById('durability-max').textContent = character.durability.max || 30;
}

// Update health display with visual indicators
function updateHealthDisplay() {
    const bodyParts = ['head', 'body', 'rightarm', 'leftarm', 'rightleg', 'leftleg', 'anima'];
    const maxHP = { head: 4, body: 8, rightarm: 6, leftarm: 6, rightleg: 6, leftleg: 6, anima: 8 };
    
    bodyParts.forEach(part => {
        const hpInput = document.getElementById(`hp-${part}`);
        const hp = parseInt(hpInput.value) || 0;
        const max = maxHP[part];
        const element = document.getElementById(`body-${part}`);
        
        character.health[part] = hp;
        
        // Remove previous classes
        element.classList.remove('low-hp', 'critical');
        
        // Add visual indicators
        if (hp === 0) {
            element.classList.add('critical');
        } else if (hp <= max * 0.3) {
            element.classList.add('low-hp');
        }
    });
    
    // Update endurance when health changes
    calculateEndurance();
    
    // Update durability when armor changes
    calculateDurability();
}

// Toggle armor display
function toggleArmorDisplay() {
    const armorEquipped = document.getElementById('armor-equipped').checked;
    const armorDisplays = ['head', 'body', 'rightarm', 'leftarm', 'rightleg', 'leftleg'];
    
    armorDisplays.forEach(part => {
        const display = document.getElementById(`armor-${part}-display`);
        if (display) {
            if (armorEquipped) {
                display.classList.remove('hidden');
            } else {
                display.classList.add('hidden');
            }
        }
    });
}

// Calculate endurance based on lost health
function calculateEndurance() {
    const maxHP = { head: 4, body: 8, rightarm: 6, leftarm: 6, rightleg: 6, leftleg: 6 };
    let totalLost = 0;
    
    Object.keys(maxHP).forEach(part => {
        const currentHP = parseInt(document.getElementById(`hp-${part}`).value) || 0;
        const max = maxHP[part];
        const lost = max - currentHP;
        totalLost += lost;
    });
    
    character.endurance.current = Math.max(0, character.endurance.max - totalLost);
    document.getElementById('endurance').textContent = character.endurance.current;
}

// Calculate durability based on lost armor
function calculateDurability() {
    const maxArmor = { head: 6, body: 24, rightarm: 6, leftarm: 6, rightleg: 6, leftleg: 6 };
    let totalLost = 0;
    
    Object.keys(maxArmor).forEach(part => {
        const currentArmor = parseInt(document.getElementById(`armor-${part}`).value) || 0;
        const max = maxArmor[part];
        const lost = max - currentArmor;
        totalLost += lost;
    });
    
    character.durability.current = Math.max(0, character.durability.max - totalLost);
    document.getElementById('durability').textContent = character.durability.current;
}

// Apply damage with armor calculation
function applyDamage() {
    const target = document.getElementById('damage-target').value;
    const damage = parseInt(document.getElementById('damage-amount').value) || 0;
    const armorEquipped = document.getElementById('armor-equipped').checked;
    
    if (damage <= 0) {
        alert('Введите урон больше 0');
        return;
    }
    
    const hpInput = document.getElementById(`hp-${target}`);
    let currentHP = parseInt(hpInput.value) || 0;
    
    if (target === 'anima') {
        // Anima doesn't use armor and doesn't affect endurance
        currentHP = Math.max(0, currentHP - damage);
        hpInput.value = currentHP;
    } else {
        if (armorEquipped) {
            // Calculate armor and body damage
            const armorInput = document.getElementById(`armor-${target}`);
            let armorHP = parseInt(armorInput.value) || 0;
            
            const armorDamage = Math.ceil(damage / 2);
            const bodyDamage = Math.floor(damage / 2);
            
            // Apply to armor first
            if (armorHP > 0) {
                const actualArmorDamage = Math.min(armorDamage, armorHP);
                armorHP -= actualArmorDamage;
                armorInput.value = armorHP;
                character.armor[target] = armorHP;
                
                // Remaining damage goes to body
                const remainingDamage = armorDamage - actualArmorDamage;
                currentHP = Math.max(0, currentHP - bodyDamage - remainingDamage);
            } else {
                // No armor HP left, all damage to body
                currentHP = Math.max(0, currentHP - damage);
            }
        } else {
            // No armor equipped, all damage directly to body
            currentHP = Math.max(0, currentHP - damage);
        }
        
        hpInput.value = currentHP;
    }
    
    character.health[target] = currentHP;
    updateHealthDisplay();
    
    // Update endurance (only for body parts, not anima)
    if (target !== 'anima') {
        calculateEndurance();
        // Update durability if armor was damaged
        if (armorEquipped && target !== 'anima') {
            calculateDurability();
        }
    }
    
    document.getElementById('damage-amount').value = 0;
}

// Reset health
function resetHealth() {
    if (!confirm('Сбросить все здоровье до максимума?')) return;
    
    document.getElementById('hp-head').value = 4;
    document.getElementById('hp-body').value = 8;
    document.getElementById('hp-rightarm').value = 6;
    document.getElementById('hp-leftarm').value = 6;
    document.getElementById('hp-rightleg').value = 6;
    document.getElementById('hp-leftleg').value = 6;
    document.getElementById('hp-anima').value = 8;
    
    document.getElementById('armor-head').value = 6;
    document.getElementById('armor-body').value = 24;
    document.getElementById('armor-rightarm').value = 6;
    document.getElementById('armor-leftarm').value = 6;
    document.getElementById('armor-rightleg').value = 6;
    document.getElementById('armor-leftleg').value = 6;
    
    character.health = {
        head: 4, body: 8, rightarm: 6, leftarm: 6,
        rightleg: 6, leftleg: 6, anima: 8
    };
    character.armor = {
        head: 6, body: 24, rightarm: 6, leftarm: 6,
        rightleg: 6, leftleg: 6
    };
    
    // Reset endurance to max
    character.endurance.current = character.endurance.max;
    document.getElementById('endurance').textContent = character.endurance.current;
    
    // Reset durability to max
    character.durability.current = character.durability.max;
    document.getElementById('durability').textContent = character.durability.current;
    
    updateHealthDisplay();
}

// Incarnate
function incarnate() {
    // Sync character.azur.current with DOM before using
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || character.azur.current || 0;
    
    if (character.azur.current < 10) {
        alert('Недостаточно Азур! Нужно 10.');
        return;
    }
    
    if (!confirm('Использовать Инкарнацию? Это восстановит все здоровье кроме Источника и потратит 10 Азур.')) return;
    
    character.azur.current -= 10;
    document.getElementById('azur-current').textContent = character.azur.current;
    document.getElementById('edit-azur-current').value = character.azur.current;
    
    // Warning at 80%+
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
    
    document.getElementById('hp-head').value = 4;
    document.getElementById('hp-body').value = 8;
    document.getElementById('hp-rightarm').value = 6;
    document.getElementById('hp-leftarm').value = 6;
    document.getElementById('hp-rightleg').value = 6;
    document.getElementById('hp-leftleg').value = 6;
    // Anima stays as is
    
    character.health = {
        head: 4, body: 8, rightarm: 6, leftarm: 6,
        rightleg: 6, leftleg: 6, anima: character.health.anima
    };
    
    // Reset endurance to max after healing
    character.endurance.current = character.endurance.max;
    document.getElementById('endurance').textContent = character.endurance.current;
    
    // Note: Durability is not reset by Incarnate (only health is healed, not armor)
    
    updateHealthDisplay();
}

// Change Azur
function changeAzur() {
    // Sync character.azur.current with DOM before changing
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || character.azur.current || 0;
    
    const change = parseInt(document.getElementById('azur-change').value) || 0;
    let newAzur = character.azur.current + change;
    
    // Auto-create neurosfera if max reached
    while (newAzur >= character.azur.max) {
        const excess = newAzur - character.azur.max;
        character.neurosferas++;
        character.azur.max += 10;
        newAzur = excess; // Remaining azur after creating neurosfera
    }
    
    character.azur.current = Math.max(0, Math.min(character.azur.max, newAzur));
    document.getElementById('azur-current').textContent = character.azur.current;
    document.getElementById('azur-max').textContent = character.azur.max;
    document.getElementById('neurosferas').textContent = character.neurosferas;
    document.getElementById('azur-change').value = 0;
    
    // Update edit form values
    document.getElementById('edit-azur-current').value = character.azur.current;
    document.getElementById('edit-azur-max').value = character.azur.max;
    document.getElementById('edit-neurosferas').value = character.neurosferas;
    
    // Warning at 80%+
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
}

// Change Neurosferas
function changeNeurosferas() {
    const change = parseInt(document.getElementById('neurosfera-change').value) || 0;
    character.neurosferas = Math.max(0, character.neurosferas + change);
    document.getElementById('neurosferas').textContent = character.neurosferas;
    document.getElementById('neurosfera-change').value = 0;
    
    // Update edit form value
    document.getElementById('edit-neurosferas').value = character.neurosferas;
}

// Spend Neurosfera
function spendNeurosfera() {
    // Sync character.azur.current with DOM before using
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || character.azur.current || 0;
    
    if (character.neurosferas <= 0) {
        alert('Нет нейросфер для траты!');
        return;
    }
    
    if (!confirm('Потратить нейросферу? Это уменьшит количество нейросфер на 1.')) return;
    
    character.neurosferas--;
    character.azur.max = Math.max(60, character.azur.max - 10); // Уменьшаем максимум на 10, минимум 60
    
    // Если текущий азур больше нового максимума, уменьшаем его
    if (character.azur.current > character.azur.max) {
        character.azur.current = character.azur.max;
    }
    
    document.getElementById('neurosferas').textContent = character.neurosferas;
    document.getElementById('azur-max').textContent = character.azur.max;
    document.getElementById('azur-current').textContent = character.azur.current;
    
    // Update edit form values
    document.getElementById('edit-azur-current').value = character.azur.current;
    document.getElementById('edit-azur-max').value = character.azur.max;
    document.getElementById('edit-neurosferas').value = character.neurosferas;
    
    // Warning at 80%+
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
}

// Edit all Azur/Neurosfera values at once
function editAzurValues() {
    const newCurrent = parseInt(document.getElementById('edit-azur-current').value);
    const newMax = parseInt(document.getElementById('edit-azur-max').value);
    const newNeurosferas = parseInt(document.getElementById('edit-neurosferas').value);
    
    if (isNaN(newCurrent) || isNaN(newMax) || isNaN(newNeurosferas)) {
        alert('Введите корректные значения!');
        return;
    }
    
    if (newCurrent < 0 || newMax < 0 || newNeurosferas < 0) {
        alert('Значения не могут быть отрицательными!');
        return;
    }
    
    if (newCurrent > newMax) {
        alert('Текущий Азур не может быть больше максимума!');
        return;
    }
    
    character.azur.current = newCurrent;
    character.azur.max = newMax;
    character.neurosferas = newNeurosferas;
    
    document.getElementById('azur-current').textContent = character.azur.current;
    document.getElementById('azur-max').textContent = character.azur.max;
    document.getElementById('neurosferas').textContent = character.neurosferas;
    
    // Update edit form with new values
    document.getElementById('edit-azur-current').value = character.azur.current;
    document.getElementById('edit-azur-max').value = character.azur.max;
    document.getElementById('edit-neurosferas').value = character.neurosferas;
    
    // Warning at 80%+
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
    
    alert('Значения обновлены!');
}

// Cast spells
function castSpell(spellName) {
    let cost = 0;
    
    switch(spellName) {
        case 'shadowTravel':
            cost = 5;
            if (character.azur.current < cost) {
                alert('Недостаточно Азур!');
                return;
            }
            character.azur.current -= cost;
            document.getElementById('azur-current').textContent = character.azur.current;
            document.getElementById('edit-azur-current').value = character.azur.current;
            alert('Переход по теням использован!');
            break;
            
        case 'shadowGrasp':
            const x = parseInt(document.getElementById('shadow-grasp-x').value) || 0;
            const source = 3; // From stats
            let baseCost = 3 + Math.floor(x * 0.5) + source;
            // Если стоимость нечетная, округляем в меньшую сторону
            if (baseCost % 2 !== 0) {
                cost = baseCost - 1;
            } else {
                cost = baseCost;
            }
            if (character.azur.current < cost) {
                alert(`Недостаточно Азур! Нужно ${cost}.`);
                return;
            }
            character.azur.current -= cost;
            document.getElementById('azur-current').textContent = character.azur.current;
            document.getElementById('edit-azur-current').value = character.azur.current;
            alert(`Теневой Захват использован! Стоимость: ${cost} Азур.`);
            break;
            
        case 'shadowVeil':
            cost = 10;
            if (character.azur.current < cost) {
                alert('Недостаточно Азур!');
                return;
            }
            character.azur.current -= cost;
            document.getElementById('azur-current').textContent = character.azur.current;
            document.getElementById('edit-azur-current').value = character.azur.current;
            const timer = document.getElementById('shadow-veil-timer');
            timer.style.display = 'block';
            timer.textContent = 'Активно: 1 минута';
            setTimeout(() => {
                timer.style.display = 'none';
            }, 60000);
            break;
            
        case 'shadowEye':
            cost = parseInt(document.getElementById('shadow-eye-cost').value) || 1;
            if (cost < 1) {
                alert('Количество Азур должно быть больше 0!');
                return;
            }
            if (character.azur.current < cost) {
                alert(`Недостаточно Азур! Нужно ${cost}.`);
                return;
            }
            character.azur.current -= cost;
            document.getElementById('azur-current').textContent = character.azur.current;
            document.getElementById('edit-azur-current').value = character.azur.current;
            const eyeTimer = document.getElementById('shadow-eye-timer');
            eyeTimer.style.display = 'block';
            eyeTimer.textContent = `Активно: наблюдение (2 Азур/мин поддержание)`;
            break;
    }
    
    // Update warning at 80%+ for all spells
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
}

// Maintain Shadow Eye
function maintainShadowEye() {
    // Sync character.azur.current with DOM before maintaining
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || character.azur.current || 0;
    
    const minutes = parseInt(document.getElementById('shadow-eye-maintenance-minutes').value) || 1;
    if (minutes < 1) {
        alert('Количество минут должно быть больше 0!');
        return;
    }
    
    const cost = minutes * 2; // 2 Азур в минуту
    if (character.azur.current < cost) {
        alert(`Недостаточно Азур! Нужно ${cost} (${minutes} мин × 2 Азур/мин).`);
        return;
    }
    
    if (!confirm(`Потратить ${cost} Азур на поддержание Глаза Тени в течение ${minutes} ${minutes === 1 ? 'минуты' : 'минут'}?`)) return;
    
    character.azur.current -= cost;
    document.getElementById('azur-current').textContent = character.azur.current;
    
    // Update edit form value
    document.getElementById('edit-azur-current').value = character.azur.current;
    
    // Warning at 80%+
    if (character.azur.current >= character.azur.max * 0.8) {
        document.getElementById('azur-warning').style.display = 'block';
    } else {
        document.getElementById('azur-warning').style.display = 'none';
    }
    
    alert(`Потрачено ${cost} Азур на поддержание Глаза Тени (${minutes} ${minutes === 1 ? 'минута' : 'минут'})`);
}

// Shotgun attack
function shotgunAttack() {
    if (character.weapons.shotgun.magazine <= 0) {
        alert('Обойма пуста! Перезарядите.');
        return;
    }
    
    const range = parseInt(document.getElementById('shotgun-range').value);
    const ammoType = document.getElementById('shotgun-ammo-type').value;
    const accuracy = 2; // Base accuracy
    const talentBonus = (range >= 5 && range <= 10) ? 1 : 0;
    
    const roll = Math.floor(Math.random() * 12) + 1;
    const total = roll + accuracy + talentBonus;
    const damage = rollDice(4, 4);
    const damageType = ammoType === 'incendiary' ? 'термический' : 'дробящий';
    
    character.weapons.shotgun.magazine--;
    document.getElementById('shotgun-magazine').value = character.weapons.shotgun.magazine;
    
    alert(`Выстрел из дробовика!\nБросок: ${roll} + ${accuracy}${talentBonus ? ' + 1 (талант)' : ''} = ${total}\nУрон: ${damage} ${damageType} урона\nДальность: ${range} фт`);
}

// Shotgun reload
function shotgunReload() {
    const ammoType = character.weapons.shotgun.ammoType;
    const available = ammoType === 'regular' 
        ? character.weapons.shotgun.regularAmmo 
        : character.weapons.shotgun.incendiaryAmmo;
    
    if (available <= 0) {
        alert('Нет патронов этого типа!');
        return;
    }
    
    const needed = 2 - character.weapons.shotgun.magazine;
    const reloaded = Math.min(needed, available);
    
    character.weapons.shotgun.magazine += reloaded;
    if (ammoType === 'regular') {
        character.weapons.shotgun.regularAmmo -= reloaded;
        document.getElementById('shotgun-regular').value = character.weapons.shotgun.regularAmmo;
    } else {
        character.weapons.shotgun.incendiaryAmmo -= reloaded;
        document.getElementById('shotgun-incendiary').value = character.weapons.shotgun.incendiaryAmmo;
    }
    
    document.getElementById('shotgun-magazine').value = character.weapons.shotgun.magazine;
    alert(`Перезарядка: +${reloaded} патронов`);
}

// Sword attack
function swordAttack() {
    const strength = 0; // From stats
    const roll = Math.floor(Math.random() * 8) + 1;
    const baseDamage = roll + strength;
    const activationBonus = character.weapons.sword.activated ? 1 : 0;
    const totalDamage = baseDamage + activationBonus;
    const damageType = character.weapons.sword.activated ? 'азурический режущий' : 'режущий';
    
    alert(`Атака мечом!\nУрон: ${roll} + ${strength}${activationBonus ? ' + 1 (активация)' : ''} = ${totalDamage} ${damageType} урона`);
}

// Sword activate
function swordActivate() {
    if (character.weapons.sword.activationsUsed >= 3) {
        alert('Достигнут лимит активаций на день!');
        return;
    }
    
    character.weapons.sword.activationsUsed++;
    character.weapons.sword.activated = true;
    character.weapons.sword.roundsLeft = 2;
    
    document.getElementById('sword-activations').value = character.weapons.sword.activationsUsed;
    document.getElementById('sword-active-indicator').style.display = 'block';
    document.getElementById('sword-rounds-left').textContent = character.weapons.sword.roundsLeft;
    
    alert('Меч активирован! +1 урон и азурическое свойство на 2 раунда.');
}

// Dice rolling
function rollD12() {
    const roll = Math.floor(Math.random() * 12) + 1;
    const resultDiv = document.getElementById('dice-result');
    resultDiv.textContent = `D12: ${roll}`;
    resultDiv.style.display = 'block';
}

function rollDice(count, sides) {
    let total = 0;
    for (let i = 0; i < count; i++) {
        total += Math.floor(Math.random() * sides) + 1;
    }
    return total;
}

function rollAttack() {
    const accuracy = 2;
    const roll = Math.floor(Math.random() * 12) + 1;
    const total = roll + accuracy;
    const resultDiv = document.getElementById('attack-result');
    resultDiv.innerHTML = `<strong>Атака:</strong> ${roll} + ${accuracy} = <strong>${total}</strong>`;
    resultDiv.style.display = 'block';
}

function useDefense() {
    const defensiveStance = document.getElementById('defensive-stance').checked;
    const bonus = defensiveStance ? 2 : 1;
    const resultDiv = document.getElementById('defense-result');
    resultDiv.innerHTML = `<strong>Оборона:</strong> Защита +${bonus}${defensiveStance ? ' (защитная стойка)' : ''}`;
    resultDiv.style.display = 'block';
}

function rollAnalysis() {
    const intelligence = 0;
    const roll = Math.floor(Math.random() * 12) + 1;
    const total = roll + intelligence;
    const resultDiv = document.getElementById('analysis-result');
    resultDiv.innerHTML = `<strong>Анализ:</strong> ${roll} + ${intelligence} = <strong>${total}</strong><br>Следующая атака: Точность +2`;
    resultDiv.style.display = 'block';
}

// Action tracking
function toggleAction(index) {
    character.actions[index - 1] = !character.actions[index - 1];
    const element = document.getElementById(`action-${index}`);
    if (character.actions[index - 1]) {
        element.classList.add('used');
    } else {
        element.classList.remove('used');
    }
}

function resetActions() {
    character.actions = [false, false, false];
    for (let i = 1; i <= 3; i++) {
        document.getElementById(`action-${i}`).classList.remove('used');
    }
}

// Save/Load
function saveCharacter() {
    // Update character data from inputs
    character.evolution = parseInt(document.getElementById('evolution').value) || 0;
    // Sync character.azur with DOM before saving
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || character.azur.current || 0;
    character.azur.max = parseInt(document.getElementById('azur-max').textContent) || 60;
    character.neurosferas = parseInt(document.getElementById('neurosferas').textContent) || 1;
    character.round = parseInt(document.getElementById('current-round').value) || 1;
    character.notes = document.getElementById('notes').value;
    character.equipment = document.getElementById('equipment').value;
    // Endurance is calculated automatically, but save max value
    character.endurance.max = parseInt(document.getElementById('endurance-max').textContent) || 12;
    // Recalculate current endurance from health
    calculateEndurance();
    // Durability is calculated automatically, but save max value
    character.durability.max = parseInt(document.getElementById('durability-max').textContent) || 30;
    // Recalculate current durability from armor
    calculateDurability();
    
    // Update health
    character.health.head = parseInt(document.getElementById('hp-head').value) || 4;
    character.health.body = parseInt(document.getElementById('hp-body').value) || 7;
    character.health.rightarm = parseInt(document.getElementById('hp-rightarm').value) || 6;
    character.health.leftarm = parseInt(document.getElementById('hp-leftarm').value) || 6;
    character.health.rightleg = parseInt(document.getElementById('hp-rightleg').value) || 6;
    character.health.leftleg = parseInt(document.getElementById('hp-leftleg').value) || 6;
    character.health.anima = parseInt(document.getElementById('hp-anima').value) || 8;
    
    // Update armor
    character.armor.head = parseInt(document.getElementById('armor-head').value) || 6;
    character.armor.body = parseInt(document.getElementById('armor-body').value) || 22;
    character.armor.rightarm = parseInt(document.getElementById('armor-rightarm').value) || 6;
    character.armor.leftarm = parseInt(document.getElementById('armor-leftarm').value) || 6;
    character.armor.rightleg = parseInt(document.getElementById('armor-rightleg').value) || 6;
    character.armor.leftleg = parseInt(document.getElementById('armor-leftleg').value) || 6;
    
    // Update weapons
    character.weapons.shotgun.magazine = parseInt(document.getElementById('shotgun-magazine').value) || 0;
    character.weapons.shotgun.regularAmmo = parseInt(document.getElementById('shotgun-regular').value) || 10;
    character.weapons.shotgun.incendiaryAmmo = parseInt(document.getElementById('shotgun-incendiary').value) || 6;
    character.weapons.shotgun.ammoType = document.getElementById('shotgun-ammo-type').value;
    character.weapons.sword.activationsUsed = parseInt(document.getElementById('sword-activations').value) || 0;
    
    // Save armor equipped state
    character.armorEquipped = document.getElementById('armor-equipped').checked;
    
    localStorage.setItem('phantomCharacter', JSON.stringify(character));
    alert('Персонаж сохранен!');
}

function loadCharacter() {
    const saved = localStorage.getItem('phantomCharacter');
    if (!saved) {
        alert('Нет сохраненных данных!');
        return;
    }
    
    if (!confirm('Загрузить сохраненного персонажа? Текущие данные будут перезаписаны.')) return;
    
    character = JSON.parse(saved);
    
    // Restore all values
    document.getElementById('evolution').value = character.evolution || 0;
    document.getElementById('azur-current').textContent = character.azur.current || 40;
    document.getElementById('azur-max').textContent = character.azur.max || 60;
    document.getElementById('neurosferas').textContent = character.neurosferas || 1;
    document.getElementById('current-round').value = character.round || 1;
    document.getElementById('notes').value = character.notes || '';
    document.getElementById('equipment').value = character.equipment || '✓ Дробовик "Зажигалочка"\n✓ Меч "Легион"\n✓ Броня "Гардиан"\n✓ Термическая граната\n✓ Переносное Хранилище';
    
    // Restore endurance max and recalculate current from health
    if (character.endurance) {
        document.getElementById('endurance-max').textContent = character.endurance.max || 12;
        // Recalculate endurance from current health
        calculateEndurance();
    }
    // Restore durability max and recalculate current from armor
    if (character.durability) {
        document.getElementById('durability-max').textContent = character.durability.max || 30;
        // Recalculate durability from current armor
        calculateDurability();
    }
    
    // Restore health
    document.getElementById('hp-head').value = character.health.head || 4;
    document.getElementById('hp-body').value = character.health.body || 7;
    document.getElementById('hp-rightarm').value = character.health.rightarm || 6;
    document.getElementById('hp-leftarm').value = character.health.leftarm || 6;
    document.getElementById('hp-rightleg').value = character.health.rightleg || 6;
    document.getElementById('hp-leftleg').value = character.health.leftleg || 6;
    document.getElementById('hp-anima').value = character.health.anima || 8;
    
    // Restore armor
    document.getElementById('armor-head').value = character.armor.head || 6;
    document.getElementById('armor-body').value = character.armor.body || 22;
    document.getElementById('armor-rightarm').value = character.armor.rightarm || 6;
    document.getElementById('armor-leftarm').value = character.armor.leftarm || 6;
    document.getElementById('armor-rightleg').value = character.armor.rightleg || 6;
    document.getElementById('armor-leftleg').value = character.armor.leftleg || 6;
    
    // Restore weapons
    document.getElementById('shotgun-magazine').value = character.weapons.shotgun.magazine || 0;
    document.getElementById('shotgun-regular').value = character.weapons.shotgun.regularAmmo || 10;
    document.getElementById('shotgun-incendiary').value = character.weapons.shotgun.incendiaryAmmo || 6;
    document.getElementById('shotgun-ammo-type').value = character.weapons.shotgun.ammoType || 'regular';
    document.getElementById('sword-activations').value = character.weapons.sword.activationsUsed || 0;
    
    // Restore armor equipped state
    document.getElementById('armor-equipped').checked = character.armorEquipped !== undefined ? character.armorEquipped : true;
    toggleArmorDisplay();
    
    // Update edit form values
    document.getElementById('edit-azur-current').value = character.azur.current || 40;
    document.getElementById('edit-azur-max').value = character.azur.max || 60;
    document.getElementById('edit-neurosferas').value = character.neurosferas || 1;
    
    updateStats();
    updateHealthDisplay();
    alert('Персонаж загружен!');
}

// Export character data to text file
function exportToFile() {
    // Update character data before export
    saveCharacter();
    
    // Create text content
    let content = `=== ДАННЫЕ ПЕРСОНАЖА: ФАНТОМ ===\n\n`;
    
    // Azur
    content += `АЗУР:\n`;
    content += `Текущий: ${character.azur.current}\n`;
    content += `Максимум: ${character.azur.max}\n`;
    content += `Нейросферы: ${character.neurosferas}\n\n`;
    
    // Health
    content += `ЗДОРОВЬЕ:\n`;
    content += `Голова: ${character.health.head} / 4\n`;
    content += `Тело: ${character.health.body} / 8\n`;
    content += `Рука Правая: ${character.health.rightarm} / 6\n`;
    content += `Рука Левая: ${character.health.leftarm} / 6\n`;
    content += `Нога Правая: ${character.health.rightleg} / 6\n`;
    content += `Нога Левая: ${character.health.leftleg} / 6\n`;
    content += `Источник: ${character.health.anima} / 8\n`;
    content += `Выносливость: ${character.endurance.current} / ${character.endurance.max}\n\n`;
    
    // Armor
    content += `БРОНЯ:\n`;
    content += `Голова: ${character.armor.head} / 6\n`;
    content += `Тело: ${character.armor.body} / 24\n`;
    content += `Рука Правая: ${character.armor.rightarm} / 6\n`;
    content += `Рука Левая: ${character.armor.leftarm} / 6\n`;
    content += `Нога Правая: ${character.armor.rightleg} / 6\n`;
    content += `Нога Левая: ${character.armor.leftleg} / 6\n`;
    content += `Прочность: ${character.durability.current} / ${character.durability.max}\n\n`;
    
    // Weapons
    content += `ОРУЖИЕ:\n`;
    content += `Дробовик - Обойма: ${character.weapons.shotgun.magazine} / 2\n`;
    content += `Дробовик - Обычные патроны: ${character.weapons.shotgun.regularAmmo}\n`;
    content += `Дробовик - Зажигательные патроны: ${character.weapons.shotgun.incendiaryAmmo}\n`;
    content += `Дробовик - Тип патронов: ${character.weapons.shotgun.ammoType}\n`;
    content += `Меч - Использовано активаций: ${character.weapons.sword.activationsUsed} / 3\n\n`;
    
    // Other
    content += `ПРОЧЕЕ:\n`;
    content += `Эволюция: ${character.evolution}\n`;
    content += `Раунд: ${character.round}\n`;
    content += `Броня надета: ${character.armorEquipped ? 'Да' : 'Нет'}\n\n`;
    
    // Notes
    if (character.notes) {
        content += `ЗАМЕТКИ:\n${character.notes}\n\n`;
    }
    
    // Equipment
    if (character.equipment) {
        content += `СНАРЯЖЕНИЕ:\n${character.equipment}\n\n`;
    }
    
    // JSON data for import
    content += `=== JSON ДАННЫЕ (для импорта) ===\n`;
    content += JSON.stringify(character, null, 2);
    
    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Фантом_Персонаж_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert('Данные экспортированы в файл!');
}

// Import character data from text file
function importFromFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        
        // Try to find JSON data in file
        const jsonMatch = content.match(/=== JSON ДАННЫЕ.*?===\n([\s\S]*)/);
        if (jsonMatch) {
            try {
                const importedCharacter = JSON.parse(jsonMatch[1]);
                
                if (!confirm('Загрузить данные из файла? Текущие данные будут перезаписаны.')) {
                    event.target.value = '';
                    return;
                }
                
                character = importedCharacter;
                loadCharacter();
                event.target.value = '';
                alert('Данные импортированы из файла!');
            } catch (error) {
                alert('Ошибка при чтении файла! Убедитесь, что файл содержит корректные данные.');
                event.target.value = '';
            }
        } else {
            // Try to parse as plain JSON
            try {
                const importedCharacter = JSON.parse(content);
                
                if (!confirm('Загрузить данные из файла? Текущие данные будут перезаписаны.')) {
                    event.target.value = '';
                    return;
                }
                
                character = importedCharacter;
                loadCharacter();
                event.target.value = '';
                alert('Данные импортированы из файла!');
            } catch (error) {
                alert('Файл не содержит данных в формате JSON. Используйте файл, экспортированный из этого листа персонажа.');
                event.target.value = '';
            }
        }
    };
    
    reader.readAsText(file);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Update sword rounds on round change
    document.getElementById('current-round').addEventListener('change', function() {
        if (character.weapons.sword.activated && character.weapons.sword.roundsLeft > 0) {
            // This is simplified - in real play, GM would track rounds
            const indicator = document.getElementById('sword-active-indicator');
            const roundsLeft = document.getElementById('sword-rounds-left');
            if (indicator && roundsLeft) {
                indicator.style.display = 'block';
                roundsLeft.textContent = character.weapons.sword.roundsLeft;
            }
        }
    });

    // Update ammo type change
    document.getElementById('shotgun-ammo-type').addEventListener('change', function() {
        character.weapons.shotgun.ammoType = this.value;
    });

    // Tooltip with delay
    let tooltipTimers = {};
    document.querySelectorAll('.tooltip-container').forEach(container => {
        container.addEventListener('mouseenter', function() {
            const timerId = this.getAttribute('data-tooltip-id') || Math.random().toString(36);
            this.setAttribute('data-tooltip-id', timerId);
            tooltipTimers[timerId] = setTimeout(() => {
                this.classList.add('show-tooltip');
            }, 1000);
        });
        
        container.addEventListener('mouseleave', function() {
            const timerId = this.getAttribute('data-tooltip-id');
            if (timerId && tooltipTimers[timerId]) {
                clearTimeout(tooltipTimers[timerId]);
                delete tooltipTimers[timerId];
            }
            this.classList.remove('show-tooltip');
        });
    });

    // Sync character.azur.current with DOM on initialization
    character.azur.current = parseInt(document.getElementById('azur-current').textContent) || 40;
    character.azur.max = parseInt(document.getElementById('azur-max').textContent) || 60;
    character.neurosferas = parseInt(document.getElementById('neurosferas').textContent) || 1;
    
    // Initialize edit form values
    document.getElementById('edit-azur-current').value = character.azur.current;
    document.getElementById('edit-azur-max').value = character.azur.max;
    document.getElementById('edit-neurosferas').value = character.neurosferas;
    
    // Initialize equipment
    if (!character.equipment) {
        character.equipment = "✓ Дробовик \"Зажигалочка\"\n✓ Меч \"Легион\"\n✓ Броня \"Гардиан\"\n✓ Термическая граната\n✓ Переносное Хранилище";
    }
    document.getElementById('equipment').value = character.equipment;
    
    // Initialize
    updateStats();
    updateHealthDisplay();
    toggleArmorDisplay();
});
