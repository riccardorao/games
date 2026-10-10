# Fantacalcio league tool

Connects to your league on [Leghe Fantacalcio](https://leghe.fantacalcio.it) with your own account and
shows your squad, your team's form, the standings, results and a pile of league statistics, in the
terminal or as a self-contained HTML dashboard.

Python 3.8+ only, no packages to install. It uses the same (unofficial, undocumented) web API the
Leghe site uses, so if Fantacalcio changes something it may need adjusting.

## Setup

Your credentials are read from the environment, or asked for when missing. They are only sent to
leghe.fantacalcio.it and are never saved.

```sh
export FANTA_USERNAME="your-username-or-email"
export FANTA_PASSWORD="your-password"      # or leave unset to be prompted
export FANTA_LEAGUE="your-league-alias"     # the part after leghe.fantacalcio.it/ ; optional if you're in one league
```

## Use

```sh
python3 fanta.py leagues          # the leagues on your account and their aliases
python3 fanta.py sync             # download everything into data/<alias>/raw.json
python3 fanta.py standings        # the table (your team marked ▶)
python3 fanta.py squad            # your squad by role and cost; `squad longo` for another team
python3 fanta.py results          # your score every round, rank in the round, opponent and result
python3 fanta.py stats            # records and trivia
python3 fanta.py dashboard        # writes data/<alias>/dashboard.html and opens it
```

Run `sync` again whenever you want fresh data; the other commands read the last download and work offline.
`-v` before the command logs every request.

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
