# План: Beta → Fanfics

Чеклист (отмечайте по мере работы):

- [ ] **Вход:** создать `.md` в папке `Beta/` (Kimi, ChatGPT и т.д.); для сессии Claude Code — `python Scripts/tools/jsonl_to_md.py Beta <session.jsonl>`
- [x] **Шапка:** в каждом файле блок `Теги:` / `Описание:` / `---` (пакетно: `python Scripts/fanfics/prepare_beta_batch.py --apply`, меню 15)
- [x] **Имена:** осмысленно переименовать черновики (`N. Краткое название.md`); для веток — `N.1. …` в Fanfics (Beta: `765..md` → осмысленные; см. `prepare_beta_batch.py`)
- [ ] **Сверка:** пункт меню «Сверка Beta ↔ Fanfics» → отчёт `Beta_vs_Fanfics_dedup_report.md` (полные дубликаты по хэшу тела после `---`)
- [ ] **Решения:** для каждого файла зафиксировать: новый номер / дубль / ветка `N.k`
- [ ] **Перенос:** из Beta в `Fanfics/` (вручную или пункт меню оркестратора)
- [ ] **Ссылки:** после появления `N.k` запустить `Scripts/fanfics/update_links.py` (покажет план), затем `--apply`
- [ ] **Нумерация:** при необходимости `python Scripts/fanfics/renumber_fanfics.py --dry-run`

Пути:

- Папка Beta: `Beta/`
- Fanfics: `Fanfics/`
- Скрипты: `Scripts/fanfics/` (`beta_fanfics_orchestrator.py`, `prepare_beta_batch.py`, `update_links.py`, `renumber_fanfics.py`)

`update_links.py` дополняет, а не перестраивает: ссылка засчитывается в любом виде
(`[[203.1. …]]`, `[[Fanfics/203.1. …]]`, с аннотацией после `]]`), аннотации сохраняются.
Удаляет он только битое — голую строку-ссылку на ветку, файла которой больше нет.
Без `--apply` ничего не пишет.

Запуск оркестратора (из корня хранилища):

```text
python Scripts/fanfics/beta_fanfics_orchestrator.py
```
