# Giochi

## Halfway

Gioco da tavolo digitale per due persone sullo stesso dispositivo. In ciascuna delle sei tappe della
vita (Famiglia, Figli, Amici, Soldi, Carriera, Tempo Libero) ognuno risponde su otto voci, senza
vedere le scelte dell'altro. Alla fine la mappa mostra dove vi incontrate a metà strada.

**Avvio:** apri `halfway/index.html` in un browser. Nessuna installazione, nessun server,
nessuna rete: lo stato vive solo in memoria e "Azzera" (in alto a destra, su ogni schermata) lo cancella del tutto.

**Flusso:** Inizia! → transizione "Tocca a [nome]" (2s) → sei aree con Indietro/Avanti (niente Indietro sulla prima) → "Ci siamo
quasi..." → transizione per il secondo giocatore (2s) → sei aree → "Fatto!" → Scopri → mappa.
I nomi sono "Giocatore 1" e "Giocatore 2" (modificabili in `DEFAULT_NAMES`).

**Come funzionano le voci**
- Ogni voce ha una domanda esplicita e una scala da 0 a 10 pallini (massimo 10 per voce).
  I pallini sono un valore concreto: per esempio *Vicinanza alle Famiglie* va da «Oltre 3 ore di
  viaggio» (0) a «Nello stesso quartiere» (10). Cinque livelli descrivono la scala: 0 · 1–3 · 4–6 · 7–9 · 10.
- Non c'è un limite ai pallini sul totale e si può sempre andare avanti. Con Indietro si torna
  alle aree già compilate del proprio turno e si ritrovano i valori.

**La dashboard finale**: sei riquadri per area con la percentuale di intesa, una sintesi a etichette
(allineati, differenza, da discutere; toccandole si apre la voce), poi la mappa: per ogni sezione un
giudizio complessivo (In Sintonia, Qualche Differenza, Un Nodo da Sciogliere, Da Discutere), l'intesa
e una riga di commento (Forza, Nodo, per chi pesa di più), poi una riga per voce con i due pallini su
una scala 0–10. In fondo il *Validity Check* e *Il Vostro Quadro*, l'analisi conclusiva: intesa globale,
profilo di coppia (la sezione a cui insieme date più peso) e sei osservazioni (Il Quadro, Le Fondamenta,
Temi di Fondo, Le Priorità, La Coerenza, Il Primo Passo).

**Come si leggono i risultati** (soglie in `T`, funzione `classify`)
- distanza ≤ 2: allineati (pilastro condiviso se entrambi ≥ 6); nessuno dei due oltre 2: poco in gioco
- distanza 3–4: sfumatura, ciascuno si sposta al massimo di 2 pallini per incontrarsi
- distanza 5–6: da negoziare
- distanza ≥ 7: da discutere (i temi di fondo, `crit`, hanno la precedenza)
- **Validity Check** (`CONFLICTS`, `validityCheck`): per ciascun giocatore, incongruenze gravi tra
  le sue risposte, cioè risposte che si escludono (es. nessun desiderio di figli ma figli subito,
  contatto quotidiano con i genitori a più di 3 ore di distanza), anche **tra sezioni diverse** (es. nessun
  desiderio di figli ma un fondo per il loro futuro, oltre 55 ore di lavoro più sport e hobby quasi ogni
  giorno). Ogni incongruenza indica se è nella stessa sezione o tra sezioni. Le voci coinvolte hanno un "!" nella mappa.
- **Intesa** (`intesa`): media della vicinanza delle risposte, pesata di più sulle voci che contano per
  almeno uno dei due e sui temi di fondo.

**Personalizzazione:** in cima allo `<script>` ci sono `MAX_PER_ITEM`, `AREAS` (aree, voci, domanda e
cinque livelli di scala), `DEFAULT_NAMES` e le soglie `T`.
