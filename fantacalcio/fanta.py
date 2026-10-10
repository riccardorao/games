#!/usr/bin/env python3
"""Fantacalcio league tool for leghe.fantacalcio.it.

Logs in with your Leghe Fantacalcio account, downloads your league's data
(squads, standings, fixtures and results, round-by-round scores, stats) and
lets you browse it from the terminal or as a self-contained HTML dashboard.

Standard library only. Credentials come from the environment
(FANTA_USERNAME, FANTA_PASSWORD) or are asked for interactively; they are
never written to disk.

    python3 fanta.py leagues                 # list the leagues on your account
    python3 fanta.py sync                    # download every league into data/<alias>/
    python3 fanta.py standings --league X    # print the table (X = part of the league name)
    python3 fanta.py squad [TEAM]            # print a squad (yours by default)
    python3 fanta.py results [TEAM]          # round-by-round scores
    python3 fanta.py stats                   # league trivia and records
    python3 fanta.py dashboard               # write dashboard.html and open it
"""

import argparse
import base64
import getpass
import html
import http.cookiejar
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE_URL = "https://leghe.fantacalcio.it/"
# Public key the Leghe web app sends with every API call (it is embedded in
# every page as `authAppKey`); refreshed from the home page when it changes.
DEFAULT_APP_KEY = "ICiELOObd5DF5uJEATi77CRvHiiRuMU0"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
TEMPLATE = HERE / "dashboard_template.html"

# League pages worth scraping: each embeds its data as `__.s('key', __.dp("<base64 json>"))`
# blocks and/or renders it as HTML tables.
PAGES = {
    "home": "",
    "classifica": "classifica",
    "calendario": "calendario",
    "rose": "rose",
    "formazioni": "formazioni",
    "hall_of_fame": "view/hall-of-fame",
    "competizioni": "lista-competizioni",
}


class FantaError(Exception):
    pass


# --------------------------------------------------------------------------- #
# HTTP client
# --------------------------------------------------------------------------- #

class Client:
    def __init__(self, verbose=False):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.app_key = DEFAULT_APP_KEY
        self.verbose = verbose
        self.user = None

    def _log(self, *a):
        if self.verbose:
            print("  ·", *a, file=sys.stderr)

    def _open(self, url, method="GET", body=None, headers=None, retries=2):
        h = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html, */*"}
        h.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(retries + 1):
            req = urllib.request.Request(url, data=data, method=method, headers=h)
            try:
                with self.opener.open(req, timeout=30) as r:
                    return r.status, r.read().decode("utf-8", "replace"), r.geturl()
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8", "replace"), url
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == retries:
                    raise FantaError(f"Network error on {url}: {e}")
                time.sleep(2 ** attempt)

    def api(self, method, path, body=None, params=None, kind="service"):
        """Call the JSON API. kind='service' -> /servizi/..., kind='action' -> /api/v1/v1_<path>."""
        url = BASE_URL + (path if kind == "service" else f"api/v1/v1_{path}")
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        self._log(method, url)
        status, text, _ = self._open(url, method, body, {"Content-Type": "application/json", "app_key": self.app_key})
        try:
            payload = json.loads(text)
        except ValueError:
            raise FantaError(f"Unexpected non-JSON reply ({status}) from {path}")
        # Some endpoints wrap the real answer as {"data": "<base64 json>"}
        if isinstance(payload, dict) and isinstance(payload.get("data"), str) and set(payload) <= {"data"}:
            payload = decode_b64_json(payload["data"])
        return payload

    def page(self, path):
        url = BASE_URL + path
        self._log("GET", url)
        status, text, final = self._open(url)
        return status, text, final

    def refresh_app_key(self):
        try:
            _, text, _ = self.page("")
            m = re.search(r'authAppKey\s*:\s*"([^"]+)"', text)
            if m:
                self.app_key = m.group(1)
        except FantaError:
            pass

    def login(self, username, password):
        self.refresh_app_key()
        res = self.api("PUT", "utente/login", {"username": username, "password": password},
                       params={"alias_lega": "login"}, kind="action")
        if not res.get("success"):
            raise FantaError("Login failed: " + error_text(res))
        self.user = res.get("data") or {}
        return self.user

    def leagues(self):
        return (self.user or {}).get("leghe") or []


def decode_b64_json(s):
    if not s:
        return None
    raw = base64.b64decode(s + "=" * (-len(s) % 4)).decode("utf-8", "replace")
    raw = raw.replace("\x00", "")
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def error_text(res):
    msgs = (res or {}).get("error_msgs") or []
    return "; ".join(m.get("descrizione") or m.get("id") or "?" for m in msgs) or "unknown error"


# --------------------------------------------------------------------------- #
# Page scraping: embedded data blocks + HTML tables
# --------------------------------------------------------------------------- #

EMBED_RE = re.compile(r"""__\.s\(\s*['"](\w+)['"]\s*,\s*__\.dp\(\s*['"]([A-Za-z0-9+/=]*)['"]""")


def extract_embedded(page_html):
    """Return {key: decoded data} for every `__.s('key', __.dp("..."))` block on a page."""
    out = {}
    for key, blob in EMBED_RE.findall(page_html):
        if not blob:
            continue
        val = decode_b64_json(blob)
        # __.dp unwraps {success, data}
        if isinstance(val, dict) and "success" in val and "data" in val:
            val = val["data"]
        out[key] = val
    return out


class TableParser(HTMLParser):
    """Collects every <table> on a page as {caption, headers, rows}, plus the nearest heading before it."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack = [], []
        self.cell = None
        self.last_heading, self._in_heading = "", False
        self._heading_buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5") and not self.stack:
            self._in_heading, self._heading_buf = True, []
        if tag == "table":
            self.stack.append({"title": self.last_heading, "headers": [], "rows": [], "row": None,
                               "cls": a.get("class", ""), "id": a.get("id", "")})
        elif not self.stack:
            return
        elif tag == "tr":
            self.stack[-1]["row"] = []
        elif tag in ("td", "th"):
            self.cell = {"th": tag == "th", "text": [], "attrs": {k: v for k, v in a.items() if k.startswith("data-")}}
        elif tag == "img" and self.cell is not None and a.get("alt"):
            self.cell["text"].append(a["alt"])

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5") and self._in_heading:
            self._in_heading = False
            self.last_heading = clean(" ".join(self._heading_buf))
        if not self.stack:
            return
        t = self.stack[-1]
        if tag in ("td", "th") and self.cell is not None and t["row"] is not None:
            t["row"].append(self.cell)
            self.cell = None
        elif tag == "tr" and t["row"] is not None:
            row = t["row"]
            t["row"] = None
            if not row:
                return
            texts = [clean(" ".join(c["text"])) for c in row]
            if all(c["th"] for c in row) and not t["rows"]:
                t["headers"] = texts
            elif any(texts):
                t["rows"].append(texts)
        elif tag == "table":
            done = self.stack.pop()
            done.pop("row", None)
            if done["rows"]:
                self.tables.append(done)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"].append(data)
        elif self._in_heading:
            self._heading_buf.append(data)


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def extract_tables(page_html):
    p = TableParser()
    try:
        p.feed(page_html)
    except Exception:
        pass
    return p.tables


# --------------------------------------------------------------------------- #
# Generic helpers for API payloads whose exact shape varies by season
# --------------------------------------------------------------------------- #

def num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("−", "-")
    if re.fullmatch(r"-?\d+(\.\d{3})*,\d+", s):
        s = s.replace(".", "").replace(",", ".")
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return default


def record_lists(obj, path=""):
    """Yield (path, list_of_dicts) for every list of objects nested anywhere in obj."""
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            yield path, obj
        for i, x in enumerate(obj[:200]):
            yield from record_lists(x, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from record_lists(v, f"{path}.{k}" if path else k)


def payload_data(res):
    if isinstance(res, dict) and "success" in res:
        return res.get("data") if res.get("success") else None
    return res


# --------------------------------------------------------------------------- #
# Sync
# --------------------------------------------------------------------------- #

def get_credentials(args):
    user = args.username or os.environ.get("FANTA_USERNAME")
    pwd = os.environ.get("FANTA_PASSWORD")
    if not user:
        user = input("Leghe Fantacalcio username or email: ").strip()
    if not pwd:
        pwd = getpass.getpass("Password: ")
    return user, pwd


def pick_league(client, wanted):
    """The league matching `wanted` (alias, name or id), or None when no league was asked for."""
    leagues = client.leagues()
    if not leagues:
        raise FantaError("This account is not in any league.")
    if wanted:
        for lg in leagues:
            if wanted.lower() in (str(lg.get("alias", "")).lower(), str(lg.get("nome", "")).lower(), str(lg.get("id"))):
                return lg
        raise FantaError(f"League '{wanted}' not found. Your leagues: " +
                         ", ".join(str(l.get("alias")) for l in leagues))
    return None  # no preference: every league


def sync(args):
    client = Client(verbose=args.verbose)
    user, pwd = get_credentials(args)
    print("Logging in…")
    client.login(user, pwd)
    league = pick_league(client, args.league or os.environ.get("FANTA_LEAGUE"))
    leagues = [league] if league else client.leagues()
    if not league and len(leagues) > 1:
        print(f"You are in {len(leagues)} leagues: " + ", ".join(str(l.get("nome") or l.get("alias")) for l in leagues))
    for lg in leagues:
        sync_league(client, lg, args)
        print()


def sync_league(client, league, args):
    alias = league.get("alias")
    print(f"League: {league.get('nome') or alias} ({alias})")

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M"), "league": league,
           "pages": {}, "embedded": {}, "api": {}, "errors": []}

    # 1. Pages: embedded data and tables
    for name, path in PAGES.items():
        try:
            status, text, final = client.page(f"{alias}/{path}")
        except FantaError as e:
            out["errors"].append(str(e))
            continue
        if status != 200:
            out["errors"].append(f"page {path or 'home'}: HTTP {status}")
            continue
        emb = extract_embedded(text)
        for k, v in emb.items():
            out["embedded"].setdefault(k, v)
        out["pages"][name] = {"url": final, "tables": extract_tables(text), "embedded_keys": sorted(emb)}
        print(f"  page {name:13s} {len(out['pages'][name]['tables'])} tables, data: {', '.join(sorted(emb)) or '-'}")

    li = out["embedded"].get("li") or {}
    league_id = first(li, "id", "id_lega") or first(league, "id")
    comp_id = first(li, "competitionId", "id_competizione") or first(league, "id_competizione")
    current_turn = int(num(first(li, "currentTurn", "giornata")) or 0)
    team_id = first(li, "teamId", "id_squadra") or first(league, "id_squadra")
    out["ids"] = {"league": league_id, "competition": comp_id, "team": team_id, "current_turn": current_turn}

    def call(name, path, **params):
        try:
            res = client.api("GET", path, params={k: v for k, v in params.items() if v not in (None, "")})
            out["api"][name] = res
            ok = (not isinstance(res, dict)) or res.get("success", True)
            print(f"  api  {name:22s} {'ok' if ok else 'error: ' + error_text(res)}")
            return payload_data(res)
        except FantaError as e:
            out["errors"].append(f"{name}: {e}")
            print(f"  api  {name:22s} failed: {e}")

    # 2. API services
    rounds = call("giornate", "servizi/V1_LegheCalcolo/Giornate", alias_lega=alias, id_competizione=comp_id)
    played = calculated_rounds(rounds, current_turn)
    out["ids"]["played_rounds"] = played
    if played:
        call("classifica", "servizi/V1_LegheCompetizione/ClassificaGiornate", alias_lega=alias,
             id_competizione=comp_id, giornata_inizio=min(played), giornata_fine=max(played))
    per_round = {}
    for g in played:
        res = call(f"round_{g}", "servizi/V1_LegheCompetizione/ClassificaGiornate", alias_lega=alias,
                   id_competizione=comp_id, giornata_inizio=g, giornata_fine=g)
        if res is not None:
            per_round[str(g)] = res
        out["api"].pop(f"round_{g}", None)
    out["rounds"] = per_round

    call("statistiche", "servizi/V1_LegheStatistiche/Statistiche", alias_lega=alias, id_lega=league_id, id_squadra=team_id)
    call("top_team", "servizi/V1_LegheStatistiche/TopTeam", alias_lega=alias, id_lega=league_id, id_squadra=team_id, d=1)
    call("albo", "servizi/V1_LegheAlbo/Storico", id_lega=league_id)
    call("live", "servizi/V1_LegheLive/Visualizza", alias_lega=alias, id_comp=comp_id, id_squadra=team_id or 0)

    # Line-ups for each played round, for your team (player votes and fantavoti)
    lineups = {}
    for g in played[-args.lineups:] if args.lineups else []:
        res = call(f"formazione_{g}", "servizi/V1_LegheFormazioni/Visualizza", alias_lega=alias,
                   id_comp=comp_id, id_squadra=team_id, giornata_lega=g)
        out["api"].pop(f"formazione_{g}", None)
        if res is not None:
            lineups[str(g)] = res
    out["lineups"] = lineups

    out["model"] = build_model(out)
    dest = DATA_DIR / alias
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "raw.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    m = out["model"]
    print(f"\nSaved to {dest / 'raw.json'}")
    print(f"  {len(m['teams'])} teams, {len(m['standings'])} standings rows, {len(m['squads'])} squads, "
          f"{len(m['scores'])} rounds of scores, {len(m['fixtures'])} fixtures")
    if out["errors"]:
        print("  Some parts could not be fetched (see 'errors' in raw.json).")


def calculated_rounds(rounds, current_turn):
    """Pick the league rounds that already have scores from the Giornate payload."""
    found = []
    for _, recs in record_lists(rounds):
        for r in recs:
            g = num(first(r, "giornata", "giornata_lega", "numero", "id_giornata", "g"))
            if g is None:
                continue
            flag = first(r, "calcolata", "calcolato", "is_calcolata", "stato", "c")
            if flag in (True, 1, "1", "true", "True", "calcolata", 2) or (flag is None and current_turn and g < current_turn):
                found.append(int(g))
        if found:
            break
    if not found and current_turn:
        found = list(range(1, current_turn))
    return sorted(set(found))


# --------------------------------------------------------------------------- #
# Normalisation into a stable model the CLI and dashboard both read
# --------------------------------------------------------------------------- #

TEAM_NAME_KEYS = ("n", "nome", "nome_squadra", "squadra", "name", "team")
TEAM_ID_KEYS = ("id_squadra", "idSquadra", "id")
ROLE_WORDS = {"p": "P", "por": "P", "d": "D", "c": "C", "a": "A"}


def build_model(raw):
    emb, api = raw.get("embedded", {}), raw.get("api", {})
    li = emb.get("li") or {}

    teams = {}
    for t in emb.get("lt") or []:
        tid = str(first(t, "id"))
        coaches = [first(c, "n", "nome", "username", default="") for c in (t.get("all") or []) if isinstance(c, dict)]
        teams[tid] = {"id": tid, "name": first(t, *TEAM_NAME_KEYS, default=f"Team {tid}"),
                      "coach": ", ".join(c for c in coaches if c), "logo": t.get("logo")}

    def team_ref(rec):
        tid = first(rec, "id_squadra", "idSquadra", "squadra_id")
        if tid is None and first(rec, "id") is not None and str(first(rec, "id")) in teams:
            tid = rec["id"]
        name = first(rec, "nome_squadra", "nome", "n", "squadra", "name")
        if tid is not None and str(tid) in teams:
            return str(tid), teams[str(tid)]["name"]
        if name and not isinstance(name, (dict, list)):
            for k, t in teams.items():
                if t["name"].lower() == str(name).lower():
                    return k, t["name"]
            return None, str(name)
        return (str(tid) if tid is not None else None), None

    my_team = str(raw.get("ids", {}).get("team") or li.get("teamId") or "")

    # ---- Standings: API first, page table as fallback
    standings = standings_from_api(payload_data(api.get("classifica")), team_ref)
    if not standings:
        standings = standings_from_table(raw.get("pages", {}).get("classifica", {}).get("tables", []))
    for i, s in enumerate(standings, 1):
        s.setdefault("pos", i)
        if not s.get("id"):
            s["id"] = team_ref({"nome": s.get("team")})[0]
        if s.get("id") and s["id"] not in teams:
            teams[s["id"]] = {"id": s["id"], "name": s["team"], "coach": "", "logo": None}

    # ---- Round-by-round fantasy scores
    scores = {}
    for g, res in sorted(raw.get("rounds", {}).items(), key=lambda kv: int(kv[0])):
        rows = standings_from_api(res, team_ref)
        sc = {}
        for r in rows:
            pts = r.get("fp")
            key = r.get("id") or r.get("team")
            if key and pts is not None:
                sc[key] = pts
        if sc:
            scores[g] = sc

    # ---- Squads
    squads = squads_from_tables(raw.get("pages", {}).get("rose", {}).get("tables", []), teams)

    # ---- Fixtures / results from the calendar page
    fixtures = fixtures_from_tables(raw.get("pages", {}).get("calendario", {}).get("tables", []))

    return {"league": {"name": first(li, "name", default=raw["league"].get("nome")),
                       "alias": raw["league"].get("alias"), "type": "Mantra" if li.get("type") == 2 else "Classic",
                       "current_turn": raw.get("ids", {}).get("current_turn")},
            "my_team": my_team, "teams": teams, "standings": standings, "scores": scores,
            "squads": squads, "fixtures": fixtures, "fetched_at": raw.get("fetched_at")}


def standings_from_api(data, team_ref):
    best = []
    for _, recs in record_lists(data):
        rows = []
        for r in recs:
            tid, name = team_ref(r)
            if not name:
                continue
            rows.append({
                "id": tid, "team": name,
                "pos": num(first(r, "posizione", "pos", "p_classifica")),
                "played": num(first(r, "giocate", "g", "partite_giocate")),
                "w": num(first(r, "vinte", "v")), "d": num(first(r, "pareggiate", "pareggi")),
                "l": num(first(r, "perse", "p_perse")),
                "gf": num(first(r, "gol_fatti", "gf")), "ga": num(first(r, "gol_subiti", "gs")),
                "pts": num(first(r, "punti", "pt", "punti_classifica")),
                "fp": num(first(r, "punti_totali", "fantapunti", "fp", "punteggio", "pt_tot", "totale", "somma")),
            })
        if len(rows) > len(best):
            best = rows
    if best and all(r["pos"] is not None for r in best):
        best.sort(key=lambda r: r["pos"])
    return best


def col(headers, *names):
    hs = [h.lower().strip(". ") for h in headers]
    for n in names:
        for i, h in enumerate(hs):
            if h == n:
                return i
    return None


def standings_from_table(tables):
    for t in tables:
        h = t["headers"]
        if not h:
            continue
        ti = col(h, "squadra", "team", "nome")
        if ti is None:
            continue
        idx = {k: col(h, *v) for k, v in {
            "pos": ("#", "pos", "posizione"), "played": ("g", "pg", "giocate"), "w": ("v",), "d": ("n", "pa"),
            "l": ("p", "s", "perse"), "gf": ("gf", "g+"), "ga": ("gs", "g-"), "pts": ("pt", "punti", "pti"),
            "fp": ("pt. totali", "pt totali", "fp", "punti totali", "tot", "fantapunti")}.items()}
        rows = []
        for i, r in enumerate(t["rows"], 1):
            g = lambda k: num(r[idx[k]]) if idx[k] is not None and idx[k] < len(r) else None
            rows.append({"id": None, "team": r[ti] if ti < len(r) else "?", "pos": g("pos") or i,
                         "played": g("played"), "w": g("w"), "d": g("d"), "l": g("l"),
                         "gf": g("gf"), "ga": g("ga"), "pts": g("pts"), "fp": g("fp")})
        if rows:
            return rows
    return []


def squads_from_tables(tables, teams):
    squads = []
    names = {t["name"].lower(): k for k, t in teams.items()}
    for t in tables:
        h = [x.lower() for x in t["headers"]]
        if not t["rows"]:
            continue
        title = t.get("title") or ""
        ri = col(t["headers"], "r", "ruolo", "ruoli")
        ni = col(t["headers"], "calciatore", "nome", "giocatore")
        ci = col(t["headers"], "costo", "crediti", "prezzo", "cr", "€")
        si = col(t["headers"], "squadra", "sq", "club")
        players = []
        for r in t["rows"]:
            if ni is None:
                # Headerless: guess role = short first cell, name = longest cell, cost = last numeric cell
                role = next((c for c in r if c.lower() in ROLE_WORDS or re.fullmatch(r"[A-Za-z]{1,3}(;[A-Za-z]{1,3})*", c)), "")
                name = max(r, key=lambda c: len(c) if not num(c) else 0)
                cost = next((num(c) for c in reversed(r) if num(c) is not None), None)
                club = ""
            else:
                role = r[ri] if ri is not None and ri < len(r) else ""
                name = r[ni] if ni < len(r) else ""
                cost = num(r[ci]) if ci is not None and ci < len(r) else None
                club = r[si] if si is not None and si < len(r) else ""
            if name and not name.lower().startswith(("totale", "crediti")):
                players.append({"role": ROLE_WORDS.get(role.lower(), role), "name": name, "club": club, "cost": cost})
        if len(players) >= 5:
            tid = names.get(title.lower())
            squads.append({"team_id": tid, "team": title or f"Squad {len(squads) + 1}", "players": players})
    return squads


def fixtures_from_tables(tables):
    fx = []
    for t in tables:
        rnd = re.search(r"(\d+)", t.get("title") or "")
        for r in t["rows"]:
            nums = [(i, num(c)) for i, c in enumerate(r) if num(c) is not None]
            texts = [(i, c) for i, c in enumerate(r) if num(c) is None and c and not re.fullmatch(r"[-–:]", c)]
            if len(texts) >= 2:
                home, away = texts[0][1], texts[-1][1]
                hs = [v for i, v in nums if texts[0][0] < i < texts[-1][0]]
                fx.append({"round": int(rnd.group(1)) if rnd else None, "home": home, "away": away,
                           "home_goals": hs[0] if len(hs) >= 2 else None, "away_goals": hs[-1] if len(hs) >= 2 else None,
                           "home_fp": hs[1] if len(hs) == 4 else None, "away_fp": hs[2] if len(hs) == 4 else None})
    return fx


# --------------------------------------------------------------------------- #
# Derived statistics
# --------------------------------------------------------------------------- #

def compute_stats(model):
    teams, scores = model["teams"], model["scores"]
    name = lambda k: teams.get(k, {}).get("name", k)
    out = {"per_team": {}, "records": []}
    if not scores:
        return out
    all_scores = [(g, k, v) for g, sc in scores.items() for k, v in sc.items()]
    keys = sorted({k for _, k, _ in all_scores})
    for k in keys:
        mine = [(int(g), sc[k]) for g, sc in scores.items() if k in sc]
        vals = [v for _, v in mine]
        # "All-play" record: how you would stand if you played every team every round
        ap_w = ap_l = ap_d = 0
        top = bottom = 0
        for g, sc in scores.items():
            if k not in sc:
                continue
            ap_w += sum(1 for o, v in sc.items() if o != k and sc[k] > v)
            ap_l += sum(1 for o, v in sc.items() if o != k and sc[k] < v)
            ap_d += sum(1 for o, v in sc.items() if o != k and sc[k] == v)
            top += sc[k] == max(sc.values())
            bottom += sc[k] == min(sc.values())
        games = ap_w + ap_l + ap_d
        out["per_team"][k] = {
            "team": name(k), "rounds": len(vals), "total": round(sum(vals), 1),
            "avg": round(statistics.mean(vals), 2), "best": max(mine, key=lambda x: x[1]),
            "worst": min(mine, key=lambda x: x[1]),
            "stdev": round(statistics.pstdev(vals), 2) if len(vals) > 1 else 0.0,
            "allplay_pct": round(100 * (ap_w + ap_d / 2) / games, 1) if games else None,
            "top_scorer_rounds": top, "wooden_spoon_rounds": bottom,
            "over_66": sum(1 for v in vals if v >= 66),
        }
    # Luck: actual table position vs. all-play position
    st = {s.get("id") or s.get("team"): s for s in model["standings"]}
    ap_rank = sorted(out["per_team"], key=lambda k: -(out["per_team"][k]["allplay_pct"] or 0))
    for i, k in enumerate(ap_rank, 1):
        out["per_team"][k]["allplay_rank"] = i
        s = st.get(k)
        if s and s.get("pos"):
            out["per_team"][k]["luck"] = int(i - s["pos"])  # positive = higher in the table than scores deserve

    g, k, v = max(all_scores, key=lambda x: x[2])
    out["records"].append(("Highest score in a round", f"{v:g}", f"{name(k)}, round {g}"))
    g, k, v = min(all_scores, key=lambda x: x[2])
    out["records"].append(("Lowest score in a round", f"{v:g}", f"{name(k)}, round {g}"))
    avg = statistics.mean(v for _, _, v in all_scores)
    out["records"].append(("League average per round", f"{avg:.1f}", f"{len(scores)} rounds"))
    rnd_avg = {g: statistics.mean(sc.values()) for g, sc in scores.items()}
    g = max(rnd_avg, key=rnd_avg.get)
    out["records"].append(("Highest-scoring round", f"{rnd_avg[g]:.1f} avg", f"round {g}"))
    g = min(rnd_avg, key=rnd_avg.get)
    out["records"].append(("Lowest-scoring round", f"{rnd_avg[g]:.1f} avg", f"round {g}"))
    pt = out["per_team"]
    k = min(pt, key=lambda k: pt[k]["stdev"])
    out["records"].append(("Most consistent", f"σ {pt[k]['stdev']}", pt[k]["team"]))
    k = max(pt, key=lambda k: pt[k]["stdev"])
    out["records"].append(("Most erratic", f"σ {pt[k]['stdev']}", pt[k]["team"]))
    lucky = [k for k in pt if "luck" in pt[k]]
    if lucky:
        k = max(lucky, key=lambda k: pt[k]["luck"])
        out["records"].append(("Luckiest", f"+{pt[k]['luck']} places", pt[k]["team"] + " (table vs. all-play)"))
        k = min(lucky, key=lambda k: pt[k]["luck"])
        out["records"].append(("Unluckiest", f"{pt[k]['luck']} places", pt[k]["team"] + " (table vs. all-play)"))
    return out


# --------------------------------------------------------------------------- #
# CLI output
# --------------------------------------------------------------------------- #

def synced_leagues():
    """{alias: raw.json path} for every league downloaded so far."""
    return {p.parent.name: p for p in sorted(DATA_DIR.glob("*/raw.json"))} if DATA_DIR.exists() else {}


def load_model(args, alias=None):
    found = synced_leagues()
    if not found:
        raise FantaError("No data yet: run `python3 fanta.py sync` first.")
    wanted = alias or args.league or os.environ.get("FANTA_LEAGUE")
    if wanted:
        def label(a):
            try:
                return a + " " + str(json.loads(found[a].read_text())["league"].get("nome") or "")
            except (ValueError, KeyError):
                return a
        matches = [a for a in found if wanted.lower() in label(a).lower()]
        if not matches:
            raise FantaError(f"No downloaded league matches '{wanted}'. Downloaded: {', '.join(found)}")
        alias = matches[0]
    elif len(found) == 1:
        alias = next(iter(found))
    else:
        raise FantaError("You have several leagues; add --league NAME (part of the name is enough). "
                         f"Downloaded: {', '.join(found)}")
    raw = json.loads(found[alias].read_text())
    raw["model"] = build_model(raw)  # rebuild so parser fixes apply to old downloads
    return raw


def table(rows, headers, aligns=None):
    rows = [["" if c is None else (f"{c:g}" if isinstance(c, float) else str(c)) for c in r] for r in rows]
    w = [max(len(str(h)), *(len(r[i]) for r in rows)) if rows else len(str(h)) for i, h in enumerate(headers)]
    aligns = aligns or ["<"] + [">"] * (len(headers) - 1)
    fmt = lambda r: "  ".join(f"{c:{a}{x}}" for c, a, x in zip(r, aligns, w))
    print(fmt(headers))
    print("  ".join("─" * x for x in w))
    for r in rows:
        print(fmt(r))


def find_team(model, q):
    if not q:
        return model["my_team"]
    q = q.lower()
    for k, t in model["teams"].items():
        if q == k or q in t["name"].lower():
            return k
    raise FantaError(f"No team matches '{q}'.")


def cmd_leagues(args):
    c = Client(verbose=args.verbose)
    c.login(*get_credentials(args))
    rows = [[l.get("alias"), l.get("nome"), l.get("id")] for l in c.leagues()]
    table(rows, ["alias", "name", "id"], ["<", "<", ">"])


def cmd_standings(args):
    m = load_model(args)["model"]
    print(f"{m['league']['name']} — standings (as of {m['fetched_at']})\n")
    rows = [[int(s["pos"]) if s.get("pos") else "", ("▶ " if s.get("id") == m["my_team"] else "  ") + s["team"],
             s.get("played"), s.get("w"), s.get("d"), s.get("l"), s.get("gf"), s.get("ga"), s.get("pts"), s.get("fp")]
            for s in m["standings"]]
    table(rows, ["#", "team", "P", "W", "D", "L", "GF", "GA", "Pts", "FP"], [">", "<"] + [">"] * 8)


def cmd_squad(args):
    m = load_model(args)["model"]
    tid = find_team(m, args.team)
    tname = m["teams"].get(tid, {}).get("name", "")
    sq = next((s for s in m["squads"] if s["team_id"] == tid or s["team"].lower() == tname.lower()), None)
    if not sq:
        raise FantaError(f"No squad found for {tname or tid}. Teams with squads: " + ", ".join(s["team"] for s in m["squads"]))
    order = {"P": 0, "D": 1, "C": 2, "A": 3}
    ps = sorted(sq["players"], key=lambda p: (order.get(p["role"][:1].upper(), 9), -(p["cost"] or 0)))
    print(f"{sq['team']} — {len(ps)} players, {sum(p['cost'] or 0 for p in ps):g} credits spent\n")
    table([[p["role"], p["name"], p["club"], p["cost"]] for p in ps], ["role", "player", "club", "cost"], ["<", "<", "<", ">"])


def cmd_results(args):
    m = load_model(args)["model"]
    tid = find_team(m, args.team)
    tname = m["teams"].get(tid, {}).get("name", tid)
    rows = []
    for g, sc in sorted(m["scores"].items(), key=lambda kv: int(kv[0])):
        if tid in sc:
            ranked = sorted(sc.values(), reverse=True)
            fx = next((f for f in m["fixtures"] if f["round"] == int(g) and tname in (f["home"], f["away"])), None)
            opp = res = ""
            if fx:
                home = fx["home"] == tname
                opp = fx["away"] if home else fx["home"]
                if fx["home_goals"] is not None:
                    a, b = (fx["home_goals"], fx["away_goals"]) if home else (fx["away_goals"], fx["home_goals"])
                    res = f"{'W' if a > b else 'L' if a < b else 'D'} {a:g}-{b:g}"
            rows.append([int(g), sc[tid], f"{ranked.index(sc[tid]) + 1}/{len(sc)}", opp, res])
    if not rows:
        raise FantaError("No round scores downloaded yet.")
    print(f"{tname} — round by round\n")
    table(rows, ["round", "FP", "rank", "opponent", "result"], [">", ">", ">", "<", "<"])


def cmd_stats(args):
    m = load_model(args)["model"]
    st = compute_stats(m)
    if not st["records"]:
        raise FantaError("Not enough round scores for statistics yet.")
    print(f"{m['league']['name']} — records\n")
    for label, val, who in st["records"]:
        print(f"  {label:26s} {val:>14s}   {who}")
    print()
    pt = st["per_team"]
    rows = sorted(pt.values(), key=lambda r: -r["total"])
    table([[r["team"], r["total"], r["avg"], f"{r['best'][1]:g} (R{r['best'][0]})", f"{r['worst'][1]:g} (R{r['worst'][0]})",
            r["stdev"], f"{r['allplay_pct']}%", r.get("luck", ""), r["top_scorer_rounds"]] for r in rows],
          ["team", "total", "avg", "best", "worst", "σ", "all-play", "luck", "top"])


def cmd_dashboard(args):
    aliases = [args.league] if args.league else list(synced_leagues())
    if not aliases:
        raise FantaError("No data yet: run `python3 fanta.py sync` first.")
    models = [dashboard_model(load_model(args, a)) for a in aliases]
    blob = json.dumps(models, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.read_text().replace("/*__DATA__*/null", blob)
    out = Path(args.out) if args.out else DATA_DIR / "dashboard.html"
    out.write_text(page)
    print(f"Dashboard with {len(models)} league(s) written to {out}")
    if not args.no_open:
        import webbrowser
        webbrowser.open(out.resolve().as_uri())


def dashboard_model(raw):
    model = raw["model"]
    model["stats"] = compute_stats(model)
    model["stats"]["records"] = [list(r) for r in model["stats"]["records"]]
    model["raw"] = {"api": raw.get("api", {}), "embedded": raw.get("embedded", {}), "lineups": raw.get("lineups", {}),
                    "tables": {k: v["tables"] for k, v in raw.get("pages", {}).items()}}
    return model


def main():
    p = argparse.ArgumentParser(description="Your Leghe Fantacalcio league in the terminal and in a dashboard.")
    p.add_argument("-v", "--verbose", action="store_true", help="log every request")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--league", help="league alias (as in leghe.fantacalcio.it/<alias>)")
        s.set_defaults(fn=fn)
        return s

    s = add("leagues", cmd_leagues, "list the leagues on your account")
    s.add_argument("--username")
    s = add("sync", sync, "download your leagues' data (all of them unless --league is given)")
    s.add_argument("--username")
    s.add_argument("--lineups", type=int, default=38, help="how many recent rounds of your line-ups to fetch (default all)")
    add("standings", cmd_standings, "league table")
    add("squad", cmd_squad, "a team's squad").add_argument("team", nargs="?", help="team name (default: yours)")
    add("results", cmd_results, "round-by-round scores").add_argument("team", nargs="?")
    add("stats", cmd_stats, "records and trivia")
    s = add("dashboard", cmd_dashboard, "build the HTML dashboard")
    s.add_argument("--out")
    s.add_argument("--no-open", action="store_true")

    args = p.parse_args()
    try:
        args.fn(args)
    except FantaError as e:
        sys.exit(f"Error: {e}")
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
