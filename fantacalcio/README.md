# Fantacalcio league tool

Connects to your league on [Leghe Fantacalcio](https://leghe.fantacalcio.it) with your own account and
shows your squad, your team's form, the standings, results and a pile of league statistics, in the
terminal or as a self-contained HTML dashboard.

Python 3.8+ only, no packages to install. It uses the same (unofficial, undocumented) web API the
Leghe site uses, so if Fantacalcio changes something it may need adjusting.

## Quick start (on your own computer)

1. Download this folder (or clone the repository) and open a terminal in `fantacalcio/`.
2. Run `python3 fanta.py sync`. It asks for your Leghe Fantacalcio username (or email) and password,
   then downloads **every league you are in**. Nothing to configure, nothing saved.
3. Run `python3 fanta.py dashboard`. It opens one page with a menu at the top to switch league.

Your password is only sent to leghe.fantacalcio.it and is never written to disk.

### Optional: skip typing the credentials every time

```sh
export FANTA_USERNAME="your-username-or-email"
export FANTA_PASSWORD="your-password"
```

## Use

```sh
python3 fanta.py leagues                    # your leagues and their short names
python3 fanta.py sync                       # download all your leagues (or: sync --league NAME for one)
python3 fanta.py dashboard                  # data/dashboard.html, with a league switcher
python3 fanta.py share                      # data/share.html: just the standings and your squad, to share
python3 fanta.py standings --league NAME    # the table (your team marked ▶)
python3 fanta.py squad --league NAME        # your squad by role and cost; add a team name for another squad
python3 fanta.py results --league NAME      # your score every round, rank in the round, opponent and result
python3 fanta.py stats --league NAME        # records and trivia
```

`NAME` can be any part of the league's name or short name (e.g. `--league amici`); with only one
league you can leave it out. Run `sync` again whenever you want fresh data; the other commands read
the last download and work offline. `-v` before the command logs every request.

## What you get

The dashboard has a menu for the league and, where a league has more than one (e.g. a cup), the competition.

- **My team**: position, points, fantasy points, average, all-play win rate, credits left, last result and
  next opponent, form, score per round against the league average, your players in and out of form.
- **Standings**: the table (by group for cups) with form, and fantasy points per team.
- **Fixtures**: any team's full calendar with results, fantasy points and rank in each round; every match of every round.
- **Squads**: every squad with what each player cost and is worth now, appearances, average vote,
  fanta-average, goals, assists and cards; squad value and credits left per team.
- **Players**: every player in the league in one sortable, searchable table.
- **Stats**: highest and lowest scores, biggest thrashing and closest match, most consistent and most
  erratic team, all-play table (your record if you'd played everyone every round), luck (table position vs.
  all-play position), a heat map of every round against the average, and player trivia: top scorer, most
  assists, best fanta-average, most cards, most expensive buy, biggest value rise, bargain of the season,
  leakiest goalkeeper.

Classic and Mantra leagues both work (Mantra roles are grouped into goalkeepers, defenders, midfielders
and forwards for sorting). Player figures are Serie A season statistics as Fantacalcio reports them.

## What it downloads

After logging in (`PUT /api/v1/v1_utente/login`), `sync` reads, for each league, the standings page of
every competition (`<alias>/classifica?id=<competition>`, which embeds the league info, teams, table and
full calendar with results), the squads page (`<alias>/rose`) and each team's player statistics
(`servizi/V1_LegheStatistiche/Statistiche`). Everything is read-only. Account tokens and your email are
dropped before anything is saved; `data/` holds your leagues' data and is git-ignored.
