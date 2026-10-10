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
python3 fanta.py standings --league NAME    # the table (your team marked ▶)
python3 fanta.py squad --league NAME        # your squad by role and cost; add a team name for another squad
python3 fanta.py results --league NAME      # your score every round, rank in the round, opponent and result
python3 fanta.py stats --league NAME        # records and trivia
```

`NAME` can be any part of the league's name or short name (e.g. `--league amici`); with only one
league you can leave it out. Run `sync` again whenever you want fresh data; the other commands read
the last download and work offline. `-v` before the command logs every request.

## What you get

- **My team**: position, league and fantasy points, average, best round, all-play win rate, score per
  round against the league average, win/draw/loss record.
- **Standings**: sortable table and fantasy-points bar chart.
- **Squads**: every squad grouped by role with what each player cost, credits spent per team.
- **Results**: any team's round-by-round scores, rank in the round, difference from the average, opponent and result; all fixtures.
- **Stats**: highest and lowest scores, best and worst rounds, most consistent and most erratic team,
  all-play table (your record if you'd played everyone every round), luck (table position vs. all-play
  position), rounds as top and bottom scorer, 66+ rounds, and a heat map of every team's round against the average.
- **Raw data**: everything downloaded (API replies, data embedded in the league pages, line-ups,
  page tables) browsable as tables, so nothing the site gives you is hidden.

## What it downloads

After logging in (`PUT /api/v1/v1_utente/login`), `sync` reads the league pages (home, classifica,
calendario, rose, formazioni, hall of fame, competitions), pulling the data each page embeds and its
HTML tables, then calls the league services: round list (`V1_LegheCalcolo/Giornate`), overall and
per-round standings (`V1_LegheCompetizione/ClassificaGiornate`), statistics and top team
(`V1_LegheStatistiche`), roll of honour (`V1_LegheAlbo/Storico`), live and your line-up each round
(`V1_LegheFormazioni/Visualizza`). Everything is read-only.

`data/` holds your league's data and is git-ignored.
