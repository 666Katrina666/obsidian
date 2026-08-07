# План: Beta → Fanfics

Чеклист (отмечайте по мере работы):

- [ ] **Вход:** либо экспорт DeepSeek JSON в Beta (п. меню оркестратора), либо вручную создать `.md` в папке `Beta/` (Kimi, ChatGPT и т.д.)
- [x] **Шапка:** в каждом файле блок `Теги:` / `Описание:` / `---` (пакетно: `python Scripts/fanfics/prepare_beta_batch.py --apply`, меню 15)
- [x] **Имена:** осмысленно переименовать черновики (`N. Краткое название.md`); для веток — `N.1. …` в Fanfics (Beta: `765..md` → осмысленные; см. `prepare_beta_batch.py`)
- [ ] **Сверка:** пункт меню «Сверка Beta ↔ Fanfics» → отчёт `Beta_vs_Fanfics_dedup_report.md` (полные дубликаты по хэшу тела после `---`)
- [ ] **Решения:** для каждого файла зафиксировать: новый номер / дубль / ветка `N.k`
- [ ] **Перенос:** из Beta в `Fanfics/` (вручную или пункт меню оркестратора)
- [ ] **Ссылки:** после появления `N.k` запустить `Scripts/fanfics/update_links.py`
- [ ] **Нумерация:** при необходимости `python Scripts/fanfics/renumber_fanfics.py --dry-run`

Пути:

- Папка Beta: `Beta/`
- Fanfics: `Fanfics/`
- Скрипты: `Scripts/fanfics/` (`beta_fanfics_orchestrator.py`, `export_deepseek_chats.py`, `update_links.py`, `renumber_fanfics.py`)

Запуск оркестратора (из корня хранилища):

```text
python Scripts/fanfics/beta_fanfics_orchestrator.py
```
