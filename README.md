# Giochi

## Halfway

Gioco da tavolo digitale per due persone sullo stesso dispositivo. In ciascuna delle sei tappe della
vita (Famiglia, Figli, Amici, Soldi, Carriera, Tempo Libero) ognuno risponde su otto voci, senza
vedere le scelte dell'altro. Alla fine la mappa mostra dove vi incontrate a metà strada.

**Avvio:** apri `halfway/index.html` in un browser. Nessuna installazione, nessun server,
nessuna rete: lo stato vive solo in memoria e "Ricomincia" lo azzera del tutto.

**Come funzionano le voci**
- Ogni voce ha un'icona, una domanda breve e una scala da 0 a 10 pallini (massimo 10 per voce).
  I pallini sono un valore concreto: per esempio *Vicinanza alle Famiglie* va da «Oltre 3 ore di
  viaggio» (0) a «Nello stesso quartiere» (10). Cinque livelli descrivono la scala: 0 · 1–3 · 4–6 · 7–9 · 10.
- Non c'è un limite ai pallini sul totale e si può sempre andare avanti: il segnale sta nelle combinazioni.
- Piccole ricompense: spunta sulle tappe completate, stella a 10 pallini, avviso a ogni tappa,
  coriandoli al passaggio del dispositivo.

**La dashboard finale**: sei riquadri con una barra colorata per area, una sintesi a etichette (allineati,
differenza, da discutere; toccandole si apre la voce), poi la mappa: una riga per voce con i due pallini
su una scala 0–10 e la barra colorata dall'esito. I dettagli si aprono al tocco. In fondo, "Sfide e Badge".

**Come si leggono i risultati** (soglie in `T`, funzione `classify`)
- distanza ≤ 2: allineati (pilastro condiviso se entrambi ≥ 6); nessuno dei due oltre 2: poco in gioco
- distanza 3–4: sfumatura, ciascuno si sposta al massimo di 2 pallini per incontrarsi
- distanza 5–6: da negoziare
- distanza ≥ 7: da discutere (i temi di fondo, `crit`, hanno la precedenza)
- **Da Chiarire / Da Conciliare** (`CONFLICTS`, `internalConflicts`): incrocia le risposte della stessa
  persona. *Da chiarire* se si escludono (nessun desiderio di figli ma un numero di figli), *da
  conciliare* se tirano in direzioni opposte (vivere accanto alle famiglie e trasferirsi ovunque), più i
  controlli «il tempo/il budget non basta per tutto» e le aree con molte voci al massimo.
- **Sfide** (`crossings`): combinazioni tra voi due che mettono in tensione le scelte
  (es. uno vuole restare vicino alle famiglie, l'altro spostarsi per lavoro).
- **Badge**: punti di forza condivisi (es. Radici Condivise, Vita in Movimento).

**Personalizzazione:** in cima allo `<script>` ci sono `MAX_PER_ITEM`, `AREAS` (aree, voci, icona,
domanda e cinque livelli di scala) e le soglie `T`. I nomi si inseriscono nella schermata iniziale.
