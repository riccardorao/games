# Giochi

- [Halfway](#halfway): gioco da tavolo per due persone
- [Fantacalcio](fantacalcio/README.md): la tua lega di Leghe Fantacalcio nel terminale e in una dashboard

## Halfway

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
esterne), pensato per essere letto a colpo d'occhio: in alto l'intesa complessiva e il profilo di coppia;
al centro una **ragnatela a 48 raggi** (una per voce, scala 0–5) con i due poligoni dei giocatori, il
punteggio di ciascuno su ogni raggio, e per ogni sezione un badge con la percentuale di intesa, uno spicchio
e un arco colorati dal giudizio; sotto **Su cosa poggiare le fondamenta** e **Dove lavorare** (punteggi,
mini-grafico a manubrio e punto d'incontro), poi il *Primo passo* e le incongruenze di ciascuno. Titoli e
cifre in Times Bold, etichette in Helvetica Bold. Nella pagina pubblicata il salvataggio passa dalla
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
