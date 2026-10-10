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
# Page scraping
# --------------------------------------------------------------------------- #

# Pages embed their data as  __.s('key', __.dp('<base64 json>'))  or  __.s('key', __.jp('<json>'[, flag]))
EMBED_RE = re.compile(r"""__\.s\(\s*'(\w+)'\s*,\s*__\.(dp|jp)\(\s*(['"])(.*?)\3\s*(?:,\s*\w+\s*)?\)\s*\)""", re.S)
# League info is a JS object literal:  var data = { name: __.ph("…"), teamId: "123", … }; __.s('li', data);
LI_RE = re.compile(r"var data = \{(.*?)\};\s*__\.s\('li', data\)", re.S)
LI_FIELD_RE = re.compile(r"""^\s*(\w+):\s*(?:__\.ph\(|__\.pb\(|Number\()?"([^"]*)"\)?\s*,?\s*$""", re.M)
COMPETITION_RE = re.compile(r"data-id='(\d+)'><span class='competition-icon competition-icon-(\d+)'></span>([^<]+)<")
# Never keep these: they identify or authenticate the account
SECRET_KEYS = {"jwt", "utente_token", "token", "email", "u"}


def extract_embedded(page_html):
    """{key: data} for every embedded data block on a league page, plus 'li' (league info)."""
    out = {}
    for key, kind, _, blob in EMBED_RE.findall(page_html):
        if key in SECRET_KEYS or not blob:
            continue
        try:
            val = decode_b64_json(blob) if kind == "dp" else json.loads(blob)
        except ValueError:
            continue
        if isinstance(val, dict) and "success" in val and "data" in val:
            val = val["data"]
        out[key] = val
    m = LI_RE.search(page_html)
    if m:
        out["li"] = {k: html.unescape(v) for k, v in LI_FIELD_RE.findall(m.group(1))}
    return out


def extract_competitions(page_html):
    seen, comps = set(), []
    for cid, icon, name in COMPETITION_RE.findall(page_html):
        if cid not in seen:
            seen.add(cid)
            comps.append({"id": cid, "kind": int(icon), "name": clean(name)})
    return comps


class RosterParser(HTMLParser):
    """The 'rose' page: one block per team (h4 = team name, h5 = coach) with a row per player,
    whose cells are tagged data-key="role|name|fvmp|team|price|cost"."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.squads, self.player, self.key, self.grab = [], None, None, None
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "h4" and "media-heading" in cls:
            self.grab, self.buf = "team", []
        elif tag == "h5" and self.squads and self.squads[-1]["coach"] is None:
            self.grab, self.buf = "coach", []
        elif tag == "tr" and a.get("data-id") and self.squads:
            self.player = {"id": a["data-id"], "role": "", "name": "", "club": "", "fvm": None, "paid": None, "value": None}
            self.squads[-1]["players"].append(self.player)
        elif tag == "td" and self.player is not None and a.get("data-key"):
            self.key, self.buf = a["data-key"], []
            if self.key == "role":
                self.player["role"] = a.get("data-roles", "")
            elif self.key == "fvmp":
                self.player["fvm"] = num(a.get("data-fvm"))

    def handle_endtag(self, tag):
        text = clean(" ".join(self.buf))
        if tag in ("h4", "h5") and self.grab:
            if self.grab == "team":
                self.squads.append({"team": text, "coach": None, "players": []})
            else:
                self.squads[-1]["coach"] = text
            self.grab = None
        elif tag == "td" and self.key:
            p = self.player
            if self.key == "name":
                p["name"] = text.title()
            elif self.key == "team" and text and "#" not in text:
                p["club"] = text  # two 'team' cells (short and full name): keep the last
            elif self.key == "price":
                p["paid"] = num(text)
            elif self.key == "cost":
                p["value"] = num(text)
            self.key = None
        elif tag == "tr":
            self.player = None

    def handle_data(self, data):
        if self.grab or self.key in ("name", "team", "price", "cost"):
            self.buf.append(data)


def extract_rosters(page_html):
    p = RosterParser()
    p.feed(page_html)
    return [s for s in p.squads if s["players"]]


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("−", "-").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def strip_secrets(obj):
    if isinstance(obj, dict):
        return {k: strip_secrets(v) for k, v in obj.items() if k not in SECRET_KEYS}
    if isinstance(obj, list):
        return [strip_secrets(x) for x in obj]
    return obj


def payload_data(res):
    if isinstance(res, dict) and res.get("success"):
        return res.get("data")
    return None


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
    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M"), "league": strip_secrets(league),
           "competitions": [], "api": {}, "errors": []}

    def page(path):
        status, text, _ = client.page(f"{alias}/{path}")
        if status != 200:
            out["errors"].append(f"{path}: HTTP {status}")
            return None
        return text

    # The standings page carries the league info, the team list and the competition menu
    text = page("classifica")
    emb = extract_embedded(text) if text else {}
    out["li"], out["teams"] = emb.get("li", {}), emb.get("lt", [])
    comps = extract_competitions(text or "")
    if not comps:
        print("  no competitions yet (the league may not have started)")
    for comp in comps:
        t = page(f"classifica?id={comp['id']}") if comp["id"] != emb.get("ci", {}).get("id") else text
        e = extract_embedded(t) if t else {}
        comp["standings"] = e.get("lr") or []
        comp["calendar"] = (e.get("ci") or {}).get("cale", {}).get("cinc") or []
        comp["info"] = {k: v for k, v in (e.get("ci") or {}).items() if k != "cale"}
        done = sum(1 for r in comp["calendar"] if r.get("cal"))
        print(f"  {comp['name']}: {len(comp['standings'])} teams in the table, {done} of {len(comp['calendar'])} rounds played")
        out["competitions"].append(comp)

    text = page("rose")
    out["rosters"] = extract_rosters(text) if text else []
    print(f"  squads: {len(out['rosters'])}")

    league_id = league.get("id")
    stats = {}
    for t in out["teams"]:
        res = client.api("GET", "servizi/V1_LegheStatistiche/Statistiche",
                         params={"alias_lega": alias, "id_lega": league_id, "id_squadra": t["id"]})
        if payload_data(res):
            stats[str(t["id"])] = payload_data(res)
    out["player_stats"] = stats
    print(f"  player stats for {len(stats)} squads")

    dest = DATA_DIR / alias
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "raw.json").write_text(json.dumps(strip_secrets(out), ensure_ascii=False, indent=1))
    print(f"  saved to {dest / 'raw.json'}")


# --------------------------------------------------------------------------- #
# Model: one tidy structure the CLI and the dashboard both read
# --------------------------------------------------------------------------- #

# Mantra roles grouped into the four classic lines (for sorting and grouping)
MANTRA_LINE = {"POR": "P", "DD": "D", "DS": "D", "DC": "D", "B": "D", "E": "C", "M": "C", "C": "C",
               "W": "A", "T": "A", "A": "A", "PC": "A"}
LINE_ORDER = {"P": 0, "D": 1, "C": 2, "A": 3}


def line_of(role):
    r = (role or "?").split(";")[0].strip().upper()
    return MANTRA_LINE.get(r, r[:1])


KIND_NAMES = {1: "League", 2: "League", 3: "Formula 1", 4: "Knockout", 5: "Groups", 6: "Cup"}


def build_model(raw):
    li = raw.get("li") or {}
    teams = {}
    for t in raw.get("teams") or []:
        tid = str(t["id"])
        teams[tid] = {"id": tid, "name": clean(t.get("n")), "coach": t.get("nu") or "",
                      "credits_left": t.get("cr"), "division": t.get("d")}
    by_name = {t["name"].lower(): k for k, t in teams.items()}

    comps = []
    for c in raw.get("competitions") or []:
        standings = [{
            "id": str(r["id"]), "team": teams.get(str(r["id"]), {}).get("name", str(r["id"])),
            "pos": r.get("pos"), "group": r.get("gr") or "", "played": r.get("g"), "w": r.get("v"), "d": r.get("n"),
            "l": r.get("pr"), "gf": r.get("gf"), "ga": r.get("gs"), "pts": r.get("p"), "fp": r.get("s_p"),
            "penalty": r.get("pen"),
        } for r in c.get("standings") or []]
        if len({s["group"] for s in standings}) <= 1:
            for s in standings:
                s["group"] = ""
        rounds, scores = [], {}
        for r in c.get("calendar") or []:
            matches = []
            for m in r.get("inc") or []:
                a, b = str(m.get("ida")), str(m.get("idb"))
                goals = re.match(r"\s*(\d+)\s*-\s*(\d+)", m.get("res") or "")
                matches.append({"home": a, "away": b, "group": m.get("gr") or "",
                                "home_fp": m.get("pa"), "away_fp": m.get("pb"),
                                "home_goals": int(goals.group(1)) if goals else None,
                                "away_goals": int(goals.group(2)) if goals else None})
            rounds.append({"round": r.get("gl"), "serie_a": r.get("ga"), "played": bool(r.get("cal")), "matches": matches})
            if r.get("cal"):
                sc = {}
                for m in matches:
                    if m["home_fp"] is not None:
                        sc[m["home"]] = m["home_fp"]
                    if m["away_fp"] is not None:
                        sc[m["away"]] = m["away_fp"]
                if sc:
                    scores[str(r.get("gl"))] = sc
        comps.append({"id": c["id"], "name": c["name"], "kind": KIND_NAMES.get(c.get("kind"), "Competition"),
                      "standings": standings, "rounds": rounds, "scores": scores})

    stats = raw.get("player_stats") or {}
    squads = []
    for s in raw.get("rosters") or []:
        tid = by_name.get(s["team"].lower())
        st = {str(p.get("id_c")): p for p in stats.get(tid, [])}
        players = []
        for p in s["players"]:
            q = st.get(p["id"])
            if q:
                apps = (q.get("g_c") or 0) + (q.get("g_f") or 0)
                tot = lambda k: (q.get(k + "_c") or 0) + (q.get(k + "_f") or 0)
                p.update({"apps": apps, "vote": q.get("vt") or None,
                          "fanta": round((q.get("vt") or 0) + (tot("b") + tot("m")) / apps, 2) if apps else None,
                          "goals": tot("gf"), "assists": tot("ass"), "yellow": tot("amm"), "red": tot("esp"),
                          "conceded": tot("gs"), "pens_saved": tot("rp"), "own_goals": tot("au"),
                          "bonus": tot("b"), "malus": tot("m"), "starts": tot("tit")})
            players.append(p)
        squads.append({"team_id": tid, "team": s["team"], "coach": s["coach"], "players": players,
                       "credits_left": teams.get(tid, {}).get("credits_left")})

    main = next((c for c in comps if c["kind"] == "League"), comps[0] if comps else None)
    my_team = str(li.get("teamId") or "")
    return {"league": {"name": li.get("name") or raw["league"].get("nome"), "alias": raw["league"].get("alias"),
                       "type": "Mantra" if str(li.get("type")) == "2" else "Classic",
                       "serie_a_round": int(num(li.get("currentTurn")) or 0)},
            "my_team": my_team, "teams": teams, "competitions": comps,
            "main": main["id"] if main else None,
            # shortcuts to the main competition, used by the CLI
            "standings": main["standings"] if main else [], "scores": main["scores"] if main else {},
            "rounds": main["rounds"] if main else [],
            "squads": squads, "fetched_at": raw.get("fetched_at")}


# --------------------------------------------------------------------------- #
# Derived statistics
# --------------------------------------------------------------------------- #

def compute_stats(model, comp=None):
    """Records and per-team figures for one competition (the main one by default)."""
    teams = model["teams"]
    comp = comp or next((c for c in model["competitions"] if c["id"] == model["main"]), None)
    scores = comp["scores"] if comp else {}
    name = lambda k: teams.get(k, {}).get("name", k)
    out = {"per_team": {}, "records": [], "players": player_records(model)}
    if not scores:
        return out
    all_scores = [(g, k, v) for g, sc in scores.items() for k, v in sc.items()]
    results = {}  # team -> list of 'W'/'D'/'L' in round order, for streaks
    margins = []
    for r in comp["rounds"]:
        for m in r["matches"]:
            if not r["played"] or m["home_goals"] is None:
                continue
            a, b = m["home_goals"], m["away_goals"]
            results.setdefault(m["home"], []).append("W" if a > b else "L" if a < b else "D")
            results.setdefault(m["away"], []).append("W" if b > a else "L" if b < a else "D")
            margins.append((abs(m["home_fp"] - m["away_fp"]), r["round"], m))
    for k in sorted({k for _, k, _ in all_scores}):
        mine = [(int(g), sc[k]) for g, sc in scores.items() if k in sc]
        vals = [v for _, v in mine]
        ap_w = ap_l = ap_d = top = bottom = 0
        for sc in scores.values():
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
            "over_66": sum(1 for v in vals if v >= 66), "form": "".join(results.get(k, [])[-5:]),
        }
    st = {s["id"]: s for s in comp["standings"]}
    ap_rank = sorted(out["per_team"], key=lambda k: -(out["per_team"][k]["allplay_pct"] or 0))
    for i, k in enumerate(ap_rank, 1):
        out["per_team"][k]["allplay_rank"] = i
        if st.get(k, {}).get("pos") and not st[k]["group"]:
            out["per_team"][k]["luck"] = int(i - st[k]["pos"])  # + = higher in the table than the scores deserve

    rec = out["records"]
    g, k, v = max(all_scores, key=lambda x: x[2])
    rec.append(("Highest score in a round", f"{v:g}", f"{name(k)}, round {g}"))
    g, k, v = min(all_scores, key=lambda x: x[2])
    rec.append(("Lowest score in a round", f"{v:g}", f"{name(k)}, round {g}"))
    rec.append(("League average per round", f"{statistics.mean(v for _, _, v in all_scores):.1f}", f"{len(scores)} rounds"))
    if margins:
        d, rnd, m = max(margins, key=lambda x: x[0])
        rec.append(("Biggest thrashing", f"{d:g} pts", f"{name(m['home'])} {m['home_fp']:g}–{m['away_fp']:g} {name(m['away'])}, round {rnd}"))
        d, rnd, m = min(margins, key=lambda x: x[0])
        rec.append(("Closest match", f"{d:g} pts", f"{name(m['home'])} {m['home_fp']:g}–{m['away_fp']:g} {name(m['away'])}, round {rnd}"))
    pt = out["per_team"]
    if len(scores) > 1:
        k = min(pt, key=lambda k: pt[k]["stdev"])
        rec.append(("Most consistent", f"σ {pt[k]['stdev']}", pt[k]["team"]))
        k = max(pt, key=lambda k: pt[k]["stdev"])
        rec.append(("Most erratic", f"σ {pt[k]['stdev']}", pt[k]["team"]))
    lucky = [k for k in pt if "luck" in pt[k]]
    if lucky and any(pt[k]["luck"] for k in lucky):
        k = max(lucky, key=lambda k: pt[k]["luck"])
        rec.append(("Luckiest", f"+{pt[k]['luck']} places", pt[k]["team"] + " (table vs. all-play)"))
        k = min(lucky, key=lambda k: pt[k]["luck"])
        rec.append(("Unluckiest", f"{pt[k]['luck']} places", pt[k]["team"] + " (table vs. all-play)"))
    return out


def player_records(model):
    """Player trivia across every squad in the league."""
    ps = [dict(p, team=s["team"]) for s in model["squads"] for p in s["players"]]
    rec = []
    played = [p for p in ps if p.get("apps")]

    def best(label, key, pool, fmt=lambda v: f"{v:g}", low=False):
        pool = [p for p in pool if p.get(key) is not None]
        if pool:
            p = (min if low else max)(pool, key=lambda p: p[key])
            if p[key]:
                rec.append((label, fmt(p[key]), f"{p['name']} ({p['team']})"))

    best("Top scorer", "goals", played)
    best("Most assists", "assists", played)
    best("Best fanta-average (3+ games)", "fanta", [p for p in played if p["apps"] >= 3], lambda v: f"{v:.2f}")
    best("Most cards", "yellow", played)
    best("Most expensive buy", "paid", ps, lambda v: f"{v:g} cr")
    best("Biggest value rise", "rise", [dict(p, rise=(p["value"] or 0) - (p["paid"] or 0)) for p in ps], lambda v: f"+{v:g}")
    bargains = [dict(p, ratio=p["fanta"] / max(p["paid"] or 1, 1)) for p in played if p.get("fanta") and p["apps"] >= 3]
    if bargains:
        p = max(bargains, key=lambda p: p["ratio"])
        rec.append(("Bargain of the season", f"{p['fanta']:.2f} for {p['paid'] or 1:g} cr", f"{p['name']} ({p['team']})"))
    keepers = [p for p in played if line_of(p["role"]) == "P" and p["apps"] >= 2]
    best("Leakiest goalkeeper (per game)", "gpg", [dict(p, gpg=p["conceded"] / p["apps"]) for p in keepers], lambda v: f"{v:.1f}")
    return rec


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
    for c in m["competitions"]:
        if not c["standings"]:
            continue
        print(f"{m['league']['name']} · {c['name']} — standings (as of {m['fetched_at']})\n")
        grouped = any(s["group"] for s in c["standings"])
        rows = [([s["group"]] if grouped else []) + [s["pos"], ("▶ " if s["id"] == m["my_team"] else "  ") + s["team"],
                 s["played"], s["w"], s["d"], s["l"], s["gf"], s["ga"], s["pts"], s["fp"]]
                for s in sorted(c["standings"], key=lambda s: (s["group"], s["pos"] or 99))]
        table(rows, (["grp"] if grouped else []) + ["#", "team", "P", "W", "D", "L", "GF", "GA", "Pts", "FP"],
              (["<"] if grouped else []) + [">", "<"] + [">"] * 8)
        print()
    if not any(c["standings"] for c in m["competitions"]):
        raise FantaError("This league has no standings yet.")


def cmd_squad(args):
    m = load_model(args)["model"]
    tid = find_team(m, args.team)
    sq = next((s for s in m["squads"] if s["team_id"] == tid), None)
    if not sq:
        raise FantaError("No squad found. Teams with squads: " + ", ".join(s["team"] for s in m["squads"]))
    ps = sorted(sq["players"], key=lambda p: (LINE_ORDER.get(line_of(p["role"]), 9), -(p["paid"] or 0)))
    print(f"{sq['team']} ({sq['coach']}) — {len(ps)} players, {sum(p['paid'] or 0 for p in ps):g} credits spent, "
          f"{sq['credits_left'] if sq['credits_left'] is not None else '?'} left\n")
    table([[p["role"], p["name"], p["club"], p["paid"], p["value"], p.get("apps"), p.get("vote"), p.get("fanta"),
            p.get("goals"), p.get("assists")] for p in ps],
          ["role", "player", "club", "paid", "value", "apps", "vote", "fanta", "goals", "assists"],
          ["<", "<", "<"] + [">"] * 7)


def cmd_results(args):
    m = load_model(args)["model"]
    tid = find_team(m, args.team)
    name = lambda k: m["teams"].get(k, {}).get("name", k)
    rows = []
    for r in m["rounds"]:
        mt = next((x for x in r["matches"] if tid in (x["home"], x["away"])), None)
        if not mt:
            continue
        home = mt["home"] == tid
        opp = mt["away"] if home else mt["home"]
        if not r["played"]:
            rows.append([r["round"], r["serie_a"], "", "", name(opp), "", ""])
            continue
        mine, theirs = (mt["home_fp"], mt["away_fp"]) if home else (mt["away_fp"], mt["home_fp"])
        a, b = (mt["home_goals"], mt["away_goals"]) if home else (mt["away_goals"], mt["home_goals"])
        sc = sorted(m["scores"].get(str(r["round"]), {}).values(), reverse=True)
        res = f"{'W' if a > b else 'L' if a < b else 'D'} {a}-{b}" if a is not None else ""
        rows.append([r["round"], r["serie_a"], mine, f"{sc.index(mine) + 1}/{len(sc)}" if mine in sc else "", name(opp), theirs, res])
    if not rows:
        raise FantaError("No fixtures for this team yet.")
    print(f"{name(tid)} — fixtures and results\n")
    table(rows, ["round", "Serie A", "FP", "rank", "opponent", "their FP", "result"], [">", ">", ">", ">", "<", ">", "<"])


def cmd_stats(args):
    m = load_model(args)["model"]
    st = compute_stats(m)
    print(f"{m['league']['name']} — records\n")
    for label, val, who in st["records"] + st["players"]:
        print(f"  {label:30s} {val:>18s}   {who}")
    pt = st["per_team"]
    if pt:
        print()
        rows = sorted(pt.values(), key=lambda r: -r["total"])
        table([[r["team"], r["total"], r["avg"], f"{r['best'][1]:g} (R{r['best'][0]})", f"{r['worst'][1]:g} (R{r['worst'][0]})",
                r["stdev"], f"{r['allplay_pct']}%", r.get("luck", ""), r["top_scorer_rounds"], r["form"]] for r in rows],
              ["team", "total", "avg", "best", "worst", "σ", "all-play", "luck", "top", "form"])
    elif not st["players"]:
        raise FantaError("No statistics yet.")


def cmd_dashboard(args):
    aliases = [args.league] if args.league else list(synced_leagues())
    if not aliases:
        raise FantaError("No data yet: run `python3 fanta.py sync` first.")
    models = [dashboard_model(load_model(args, a)) for a in aliases]
    models.sort(key=lambda m: not (m["competitions"] or m["squads"]))  # leagues that haven't started go last
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
    model["stats"] = {c["id"]: compute_stats(model, c) for c in model["competitions"]}
    model["player_records"] = player_records(model)
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
    except BrokenPipeError:  # output piped into `head` and the like
        sys.stderr.close()


if __name__ == "__main__":
    main()
