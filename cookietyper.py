#!/usr/bin/env python3
"""
Cookie Typer  —  cookie clicker s twistem.
Body (sušenky) nedostáváš za klikání, ale za OPISOVÁNÍ textu.
Čím rychleji a přesněji píšeš, tím víc sušenek. Pak utrácíš za upgrady.

Statické TUI: obrazovka se překresluje na místě, nescrolluje.
Incognito mód ('i' nebo --incognito): převlékne hru za nudný
stream-processor, aby na první pohled nevypadala jako hra.

Spuštění:  python3 cookietyper.py
"""

import json
import os
import random
import sys
import threading
import time

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")

# ── ANSI ───────────────────────────────────────────────────────────────────
class C:
    R = "\033[0m"; DIM = "\033[2m"; B = "\033[1m"
    GOLD = "\033[38;5;220m"; BROWN = "\033[38;5;130m"; GREEN = "\033[38;5;42m"
    RED = "\033[38;5;203m"; CYAN = "\033[38;5;45m"; GREY = "\033[38;5;245m"
    YEL = "\033[38;5;227m"; BLUE = "\033[38;5;39m"

def _supports_color():
    return sys.stdout.isatty() and os.environ.get("TERM") not in (None, "dumb")

if not _supports_color():
    for k in list(vars(C)):
        if k.isupper():
            setattr(C, k, "")

CLEAR = "\033[2J\033[H"
HIDE = "\033[?25l"; SHOW = "\033[?25h"
SAVECUR = "\0337"; LOADCUR = "\0338"     # ulož / obnov pozici kurzoru

LIVE = sys.stdout.isatty()               # živý update jen v interaktivním terminálu
_lock = threading.Lock()                 # synchronizace kreslení mezi vlákny

# ── Texty k opisování ──────────────────────────────────────────────────────
SNIPPETS = [
    "the quick brown fox jumps over the lazy dog",
    "sušenky se nejlépe pečou v rozpálené troubě",
    "git commit -m fix opraven pad pri startu",
    "rychlost je nic platná bez přesnosti psaní",
    "import os sys json from the standard library",
    "kdo rychle píše ten dvakrát programuje",
    "list comprehension je elegantní způsob iterace",
    "every keystroke brings another warm cookie",
    "deset prstů na klávesnici je tajná zbraň",
    "refactor early refactor often but test always",
    "káva klávesnice a klid v duši stačí ke štěstí",
    "the terminal is the only interface you need",
    "prokrastinace je nepřítel produktivního psaní",
    "napsat řádek kódu je lepší než o něm mluvit",
]

# ── Obchod ─────────────────────────────────────────────────────────────────
# kind: gen=pasivní/s · pow=+za znak · mult=globální násobič
# name=herní popisek, alt=incognito popisek
SHOP = [
    {"id": "intern",  "name": "Stážista",             "alt": "io.reader",     "kind": "gen",  "val": 0.5, "cost": 50,     "rate": 1.15},
    {"id": "keyb",    "name": "Mechanická klávesnice", "alt": "buffer.x2",     "kind": "pow",  "val": 2,   "cost": 120,    "rate": 1.20},
    {"id": "typist",  "name": "Písař na plný úvazek",  "alt": "worker.pool",   "kind": "gen",  "val": 3,   "cost": 400,    "rate": 1.15},
    {"id": "ergo",    "name": "Ergonomický setup",     "alt": "cache.layer",   "kind": "pow",  "val": 5,   "cost": 1100,   "rate": 1.22},
    {"id": "steno",   "name": "Stenograf",            "alt": "batch.proc",    "kind": "gen",  "val": 16,  "cost": 2600,   "rate": 1.15},
    {"id": "energy",  "name": "Energy drink",         "alt": "jit.compile",   "kind": "mult", "val": 1.5, "cost": 6000,   "rate": 1.40},
    {"id": "ai",      "name": "AI našeptávač",         "alt": "async.queue",   "kind": "gen",  "val": 90,  "cost": 14000,  "rate": 1.15},
    {"id": "macro",   "name": "Makro farma",          "alt": "shard.cluster", "kind": "gen",  "val": 480, "cost": 90000,  "rate": 1.15},
    {"id": "quantum", "name": "Kvantová klávesnice",  "alt": "vectorize.simd","kind": "mult", "val": 2.0, "cost": 250000, "rate": 1.55},
]

# ── Skiny (běžný vs incognito) ─────────────────────────────────────────────
SKINS = {
    False: {  # herní vzhled
        "accent": C.GOLD, "prompt": "cookie>", "coin": "🍪",
        "title": "🍪 COOKIE TYPER", "subtitle": "vydělávej sušenky opisováním textu",
        "unit": "sušenek", "rate": "/s", "power": "/znak", "mult": "x",
        "shop_title": "OBCHOD", "shop_hint": "napiš číslo pro koupi",
        "buy_ok": "Koupeno", "type_title": "OPIŠ TENTO TEXT",
        "type_hint": "co nejrychleji a nejpřesněji",
        "earned": "sušenek!", "perfect": "✦ Perfektní opis!",
        "foot": "Enter = opiš text a vydělej · číslo = kup · q = konec",
        "newgame": "Nová hra. Stiskni Enter a začni psát!",
        "bye": "Měj se, šampione klávesnice! 🍪",
    },
    True: {  # incognito: tváří se jako stream processor
        "accent": C.BLUE, "prompt": "dataproc$", "coin": "",
        "title": "dataproc 2.4.1", "subtitle": "distributed stream processor — live",
        "unit": "records", "rate": " rec/s", "power": " thr/op", "mult": "f",
        "shop_title": "PIPELINE MODULES", "shop_hint": "type id to deploy",
        "buy_ok": "Module deployed", "type_title": "MANUAL VALIDATION REQUIRED",
        "type_hint": "retype record below to verify checksum",
        "earned": "records committed", "perfect": "checksum OK",
        "foot": "[enter] validate batch · [id] deploy module · [q] quit",
        "newgame": "Session started. Press [enter] to validate first batch.",
        "bye": "Connection closed.",
    },
}

def sk(s):
    return SKINS[bool(s.get("incognito"))]

def shop_name(s, it):
    return it["alt"] if s.get("incognito") else it["name"]

def new_state():
    return {"cookies": 0.0, "total_earned": 0.0, "chars_typed": 0,
            "best_wpm": 0.0, "owned": {}, "last_tick": time.time(),
            "incognito": False}

# ── Výpočty ────────────────────────────────────────────────────────────────
def item_cost(it, owned):
    return int(it["cost"] * (it["rate"] ** owned.get(it["id"], 0)))

def per_char_power(s):
    return 1.0 + sum(it["val"] * s["owned"].get(it["id"], 0)
                     for it in SHOP if it["kind"] == "pow")

def global_mult(s):
    m = 1.0
    for it in SHOP:
        if it["kind"] == "mult":
            m *= it["val"] ** s["owned"].get(it["id"], 0)
    return m

def cps(s):
    base = sum(it["val"] * s["owned"].get(it["id"], 0)
               for it in SHOP if it["kind"] == "gen")
    return base * global_mult(s)

def tick(s):
    now = time.time()
    dt = now - s["last_tick"]
    s["last_tick"] = now
    if dt > 0:
        gain = cps(s) * dt
        s["cookies"] += gain
        s["total_earned"] += gain

def fmt(n):
    n = float(n)
    for u in ["", "k", "M", "B", "T"]:
        if abs(n) < 1000:
            return f"{int(n)}{u}" if (u == "" and n == int(n)) else f"{n:.1f}{u}"
        n /= 1000
    return f"{n:.1f}Q"

# ── Statické vykreslení ────────────────────────────────────────────────────
W = 60

def line(text="", pad=2):
    print(" " * pad + text)

def rule():
    print(C.DIM + " " * 2 + "─" * (W - 2) + C.R)

STATS_ROW = 3   # řádek, na kterém je stav (kvůli live updatu)

def stats_text(s):
    """Obsah řádku se stavem (bez levého odsazení)."""
    t = sk(s)
    A = t["accent"]
    return (f"{A}{C.B}{fmt(s['cookies']):>10} {t['unit']}{C.R}   "
            f"{C.GREEN}{fmt(cps(s))}{t['rate']}{C.R}   "
            f"{C.GREY}+{fmt(per_char_power(s))}{t['power']} · "
            f"{t['mult']}{global_mult(s):.2f}{C.R}")

def draw(s, message=""):
    t = sk(s)
    A = t["accent"]
    sys.stdout.write(CLEAR)
    line(f"{A}{C.B}{t['title']}{C.R}   {C.GREY}{t['subtitle']}{C.R}")
    rule()
    coin = t["coin"]
    line(stats_text(s))
    rule()
    line(f"{C.B}{t['shop_title']}{C.R} {C.GREY}— {t['shop_hint']}{C.R}")
    for i, it in enumerate(SHOP, 1):
        owned = s["owned"].get(it["id"], 0)
        cost = item_cost(it, s["owned"])
        afford = s["cookies"] >= cost
        col = C.GREEN if afford else C.GREY
        mark = "●" if afford else "○"
        if it["kind"] == "gen":   eff = f"+{fmt(it['val'])}{t['rate']}"
        elif it["kind"] == "pow": eff = f"+{it['val']}{t['power']}"
        else:                     eff = f"{t['mult']}{it['val']}"
        line(f"{col}{mark} {i:>2}. {shop_name(s, it):<22}{C.R}"
             f"{A}{fmt(cost):>8}{coin}{C.R} "
             f"{C.DIM}{eff:<11}{C.R}{C.CYAN}x{owned}{C.R}")
    rule()
    if message:
        for ln in message.split("\n"):
            line(ln)
    else:
        line(f"{C.GREY}{t['foot']}{C.R}")
    rule()

# ── Akce ───────────────────────────────────────────────────────────────────
def do_type(s):
    t = sk(s)
    text = random.choice(SNIPPETS)
    sys.stdout.write(CLEAR)
    line(f"{C.CYAN}{C.B}{t['type_title']}{C.R} {C.GREY}({t['type_hint']}){C.R}")
    rule()
    line(f"{C.B}{C.YEL}{text}{C.R}")
    rule()
    sys.stdout.write(SHOW)
    try:
        start = time.time()
        typed = input("  > ")
        elapsed = max(time.time() - start, 0.001)
    except (EOFError, KeyboardInterrupt):
        return f"{C.GREY}aborted.{C.R}"

    correct = sum(1 for a, b in zip(typed, text) if a == b)
    accuracy = correct / len(text)
    wpm = len(text.split()) / (elapsed / 60.0)
    speed_bonus = 1.0 + min(wpm, 200) / 100.0
    earned = correct * per_char_power(s) * accuracy * speed_bonus * global_mult(s)

    s["cookies"] += earned
    s["total_earned"] += earned
    s["chars_typed"] += correct
    s["best_wpm"] = max(s["best_wpm"], wpm)

    acc_col = C.GREEN if accuracy > 0.95 else (C.YEL if accuracy > 0.7 else C.RED)
    msg = (f"{sk(s)['accent']}{C.B}+{fmt(earned)} {t['earned']}{C.R}   "
           f"{acc_col}{accuracy*100:.0f}%{C.R} · "
           f"{C.CYAN}{wpm:.0f} WPM{C.R} · "
           f"{C.GREY}x{speed_bonus:.2f}{C.R}")
    if accuracy == 1.0:
        msg += f"\n{C.GREEN}{t['perfect']}{C.R}"
    return msg

def do_buy(s, idx):
    t = sk(s)
    it = SHOP[idx]
    cost = item_cost(it, s["owned"])
    if s["cookies"] < cost:
        return f"{C.RED}{shop_name(s, it)}: need {fmt(cost)}{t['coin']}.{C.R}"
    s["cookies"] -= cost
    s["owned"][it["id"]] = s["owned"].get(it["id"], 0) + 1
    return f"{C.GREEN}{t['buy_ok']}: {shop_name(s, it)} (x{s['owned'][it['id']]}).{C.R}"

def stats_msg(s):
    if s.get("incognito"):
        return (f"{C.B}METRICS{C.R}  "
                f"total {C.GREEN}{fmt(s['total_earned'])}{C.R} · "
                f"bytes {C.CYAN}{s['chars_typed']}{C.R} · "
                f"peak {C.CYAN}{s['best_wpm']:.0f}{C.R} ops · "
                f"modules {C.CYAN}{sum(s['owned'].values())}{C.R}")
    return (f"{C.B}STATISTIKY{C.R}  "
            f"celkem {C.GOLD}{fmt(s['total_earned'])}{C.R}🍪 · "
            f"znaků {C.CYAN}{s['chars_typed']}{C.R} · "
            f"nej WPM {C.CYAN}{s['best_wpm']:.0f}{C.R} · "
            f"věcí {C.CYAN}{sum(s['owned'].values())}{C.R}")

# ── Save / Load ────────────────────────────────────────────────────────────
def save(s):
    s["last_tick"] = time.time()
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(s, f)
        return f"{C.GREEN}saved.{C.R}"
    except OSError as e:
        return f"{C.RED}save failed: {e}{C.R}"

def load():
    if not os.path.exists(SAVE_PATH):
        return None
    try:
        with open(SAVE_PATH) as f:
            data = json.load(f)
        s = new_state()
        s.update(data)
        s["last_tick"] = time.time()
        return s
    except (OSError, json.JSONDecodeError):
        return None

# ── Živý update čítače ─────────────────────────────────────────────────────
class Live(threading.Thread):
    """Na pozadí překresluje jen řádek se stavem, aby čítač sušenek
    běžel v reálném čase i během čekání na vstup. Rozepsaný příkaz
    nerozhází — pozici kurzoru si uloží a vrátí."""
    def __init__(self, s, interval=0.25):
        super().__init__(daemon=True)
        self.s = s
        self.interval = interval
        self.on = False        # překreslovat?
        self.stopped = False

    def run(self):
        while not self.stopped:
            if self.on:
                with _lock:
                    tick(self.s)
                    sys.stdout.write(
                        SAVECUR + f"\033[{STATS_ROW};1H\033[2K  "
                        + stats_text(self.s) + LOADCUR)
                    sys.stdout.flush()
            time.sleep(self.interval)


# ── Hlavní smyčka ──────────────────────────────────────────────────────────
def main():
    start_incognito = any(a in ("-i", "--incognito", "--stealth") for a in sys.argv[1:])
    s = load() or new_state()
    if start_incognito:
        s["incognito"] = True
    message = (f"{C.GREEN}saved session restored.{C.R}" if os.path.exists(SAVE_PATH)
               else f"{C.GREY}{sk(s)['newgame']}{C.R}")
    live = Live(s)
    if LIVE:
        live.start()
    try:
        while True:
            live.on = False
            with _lock:
                tick(s)
                sys.stdout.write(HIDE)
                draw(s, message)
                sys.stdout.write(SHOW)
            live.on = True
            try:
                raw = input(f"  {sk(s)['accent']}{sk(s)['prompt']}{C.R} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                save(s); break
            live.on = False

            if raw == "":
                message = do_type(s)
            elif raw.isdigit():
                n = int(raw) - 1
                message = (do_buy(s, n) if 0 <= n < len(SHOP)
                           else f"{C.RED}no item {raw}.{C.R}")
            elif raw in ("t", "type"):
                message = do_type(s)
            elif raw in ("s", "stats"):
                message = stats_msg(s)
            elif raw in ("i", "incognito"):
                s["incognito"] = not s.get("incognito")
                message = ""  # ať se nic neprozradí
            elif raw == "save":
                message = save(s)
            elif raw in ("q", "quit", "exit"):
                save(s); break
            elif raw in ("h", "help", "?"):
                message = (f"{C.CYAN}enter{C.R}=type/validate · "
                           f"{C.CYAN}id{C.R}=buy/deploy · "
                           f"{C.CYAN}s{C.R}=stats · {C.CYAN}i{C.R}=incognito · "
                           f"{C.CYAN}q{C.R}=quit")
            else:
                message = f"{C.RED}unknown '{raw}'. [enter] [id] [q]{C.R}"
    finally:
        live.stopped = True
        sys.stdout.write(SHOW)
        print(f"\n  {C.GREY}{sk(s)['bye']}{C.R}")

if __name__ == "__main__":
    main()
