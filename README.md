# Games

## Halfway

A digital board game for two people on the same device. In each of six stages of life (Family, Children,
Friends, Money, Career, Free Time) each of you answers eight items without seeing the other's choices. At
the end the map shows where you meet halfway.

**To play:** open `halfway/index.html` in a browser. No installation, no server, no network: the state lives
in memory only, and "Start Over" wipes it completely.

**How the items work**
- Each item has an icon, a short question and a scale of 0 to 10 dots (10 at most per item). The dots stand
  for something concrete: *Close to Family*, for example, runs from "Over 3 hours away" (0) to "In the same
  neighbourhood" (10). Five levels describe the scale: 0 · 1–3 · 4–6 · 7–9 · 10.
- There is no cap on the total and you can always move on: the signal is in the combinations.
- Small rewards: a tick on finished stages, a star at 10 dots, a notice at each stage, confetti when the
  device is passed over.

**The final dashboard**: six tiles with a coloured bar per area, a tag summary (aligned, different, to talk
through; tapping one opens the item), then the map: one row per item with both players' dots on a 0–10 scale
and a bar coloured by the outcome. Details open on tap. At the bottom, "Challenges and Badges".

**How to read the results** (thresholds in `T`, function `classify`)
- distance ≤ 2: aligned (a shared pillar if both are ≥ 6); neither above 2: little at stake
- distance 3–4: a nuance, each moves at most 2 dots to meet
- distance 5–6: to negotiate
- distance ≥ 7: to talk through (underlying themes, `crit`, come first)
- **To Clarify / To Reconcile** (`CONFLICTS`, `internalConflicts`): cross-checks one person's own answers.
  *To clarify* if they rule each other out (no wish for children, but a number of children), *to reconcile*
  if they pull in opposite directions (living next to family and moving anywhere), plus the "not enough
  time / money for everything" checks and areas with many items at the top.
- **Challenges** (`crossings`): combinations between the two of you that put your choices under strain
  (one wants to stay near family, the other to move for work, for example).
- **Badges**: shared strengths (Shared Roots, A Life on the Move…).

**Customising:** at the top of the `<script>` are `MAX_PER_ITEM`, `AREAS` (areas, items, icon, question
and the five levels of the scale) and the thresholds `T`. Names are entered on the start screen.

## Spades Scorer

A scorekeeper for the card game Spades, in a single page: `picche/index.html`. No server, no installation,
works offline. Scores stay in the browser of whoever opens the page.

### Use

1. Open `picche/index.html`.
2. The first time: names, mode (partners, or individual with 3–5 players), target score and tricks per hand.
3. For each hand enter every player's bid and tricks (+/− buttons, typing, up/down arrows, Enter for the
   next field). The `nil` button cycles through nil and blind nil.
4. When the tricks add up, **Record**.

In the ledger, tap a row to correct it and × to delete it: bags and penalties are recalculated across the
whole game.

### Scoring

Standard values, editable from the … menu → Scoring rules:

| Item | Default |
| --- | --- |
| Trick bid | 10 pts (negative if the contract fails) |
| Bag | 1 pt, a 100-point penalty every 10 bags |
| Nil | ±100, blind ±200 |

### The … menu

Players and game, Scoring rules, Backup (copy/paste the game as text to move it elsewhere), Undo last hand,
Clear the ledger (deletes the hands only).

Games saved by the earlier Italian version (Segnapicche, and before it Sacchi e Picche) still load: the
storage keys are unchanged.
Gioco da tavolo digitale per due persone sullo stesso dispositivo. In ciascuna delle sei tappe della
vita (Famiglia, Figli, Amici, Soldi, Carriera, Tempo Libero) ognuno risponde su otto voci, senza
vedere le scelte dell'altro. Alla fine la mappa mostra dove vi incontrate a metà strada.

**Avvio:** apri `halfway/index.html` in un browser. Nessuna installazione, nessun server,
nessuna rete: lo stato vive solo in memoria e "Azzera" (in alto a destra, su ogni schermata) lo cancella del tutto.

**Lingua:** nella home si sceglie italiano o inglese; tutto il gioco, la dashboard e il PDF seguono la
lingua scelta (che resta anche dopo "Azzera").

**Flusso:** Inizia! → transizione "Tocca a [nome]" (2s) → sei aree con Indietro/Avanti (niente Indietro sulla prima) → "Ci siamo
quasi..." → transizione per il secondo giocatore (2s) → sei aree → "Fatto!" → Scopri → mappa.
Nella home si possono scrivere i nomi dei due giocatori (facoltativi, max 20 caratteri); se restano vuoti si usano "Giocatore 1" e "Giocatore 2" (o "Player 1" e "Player 2").

**Come funzionano le voci**
- Ogni voce ha una domanda esplicita e una scala da 0 a 5 pallini, e **ogni valore ha la sua risposta**:
  per esempio *Vicinanza alle Famiglie* va da «Oltre 3 ore di viaggio» (0) a «2–3 ore», «Circa un'ora»,
  «Entro 30 minuti», «Nella stessa città» fino a «Nello stesso quartiere» (5).
- Non c'è un limite ai pallini sul totale e si può sempre andare avanti. Con Indietro si torna
  alle aree già compilate del proprio turno e si ritrovano i valori.

**La dashboard finale**: sei riquadri per area con la percentuale di intesa, una sintesi a etichette
(allineati, differenza, da discutere; toccandole si apre la voce), poi la mappa: per ogni sezione un
giudizio complessivo (In Sintonia, Qualche Differenza, Un Nodo da Sciogliere, Da Discutere), l'intesa
e una riga di commento (Forza, Nodo, per chi pesa di più), poi una riga per voce con i due pallini su
una scala 0–5. In fondo il *Validity Check* e *Il Vostro Quadro*, l'analisi conclusiva: intesa globale,
profilo di coppia (la sezione a cui insieme date più peso) e sei osservazioni (Il Quadro, Le Fondamenta,
Temi di Fondo, Le Priorità, La Coerenza, Il Primo Passo).

**Esporta PDF**: in cima e in fondo alla dashboard. Genera un PDF A4 di una pagina (senza librerie
esterne) con intesa e profilo di coppia, la sintesi di ogni sezione (esito, intesa, commento e le otto voci
con i due pallini) e le sei osservazioni finali. Nella pagina pubblicata il salvataggio passa dalla
conferma di download di claude.ai; aperto come file locale è un normale download.

**Come si leggono i risultati** (soglie in `T`, funzione `classify`)
- distanza ≤ 1: allineati (pilastro condiviso se entrambi ≥ 3); nessuno dei due oltre 1: poco in gioco
- distanza 2: sfumatura, ciascuno si sposta di un pallino per incontrarsi
- distanza 3: da negoziare
- distanza ≥ 4: da discutere (i temi di fondo, `crit`, hanno la precedenza)
- **Validity Check** (`CONFLICTS`, `validityCheck`): per ciascun giocatore, incongruenze gravi tra
  le sue risposte, cioè risposte che si escludono (es. nessun desiderio di figli ma figli subito,
  contatto quotidiano con i genitori a più di 3 ore di distanza), anche **tra sezioni diverse** (es. nessun
  desiderio di figli ma un fondo per il loro futuro, oltre 55 ore di lavoro più sport e hobby quasi ogni
  giorno). Ogni incongruenza indica se è nella stessa sezione o tra sezioni. Le voci coinvolte hanno un "!" nella mappa.
- **Intesa** (`intesa`): media della vicinanza delle risposte, pesata di più sulle voci che contano per
  almeno uno dei due e sui temi di fondo.

**Personalizzazione:** in cima allo `<script>` ci sono `MAX_PER_ITEM`, `AREAS` (aree, voci, domanda e
sei risposte, in italiano e inglese), le soglie `T` e i testi dell'interfaccia in `STR`.
