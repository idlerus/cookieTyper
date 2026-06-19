# 🍪 Cookie Typer

Cookie clicker s twistem: **sušenky nedostáváš za klikání, ale za opisování textu.**
Čím rychleji a přesněji píšeš, tím víc vyděláš — a pak utrácíš za upgrady, co píšou za tebe.

Celé je to jeden Python soubor, žádné závislosti, běží v terminálu.

## Spuštění

```bash
python3 cookietyper.py
```

## Ovládání

Statické TUI — obrazovka se překresluje na místě (nescrolluje). Obchod je pořád vidět.

| Vstup | Akce |
|-------|------|
| `Enter` | dostaneš text k opsání → vyděláš sušenky |
| `1`–`9` | koupíš upgrade s daným číslem |
| `s` | statistiky |
| `i` | přepne **incognito mód** |
| `save` | uloží hru |
| `q` | uloží a ukončí |

## Mechaniky

- **Skóre za opis** = `znaky × síla/znak × přesnost × bonus_za_rychlost × násobič`
- **Tři typy upgradů (18 položek):** generátory (pasivní sušenky/s, běží i offline; páteř ekonomiky), síla (víc za znak) a dva globální násobiče
- **Násobiče se sčítají, ne umocňují** — 2× stejný násobič (×3) = ×6, ne ×9, takže pozdní hra neexploduje
- **Cenový scaling:** každý kus stojí `base × 1.5^vlastněno`; base ceny tierů rostou ~7,6× (= 1.5⁵), takže další tier se vyplatí zhruba od 5 kusů předchozího
- **Pasivní příjem** se počítá podle reálně uplynulého času, i mezi spuštěními
- Postup se ukládá do `save.json`

## 🕵️ Incognito mód

Stiskni `i` (nebo spusť `python3 cookietyper.py --incognito`) a hra se převlékne
za nudný stream processor — žádné sušenky, jen `records`, `rec/s` a `PIPELINE MODULES`.
Na první pohled to nevypadá jako hra.

## Licence

MIT
