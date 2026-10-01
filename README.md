# Giochi

## La nostra mappa

Gioco da tavolo digitale per due persone sullo stesso dispositivo. In ciascuna delle sei aree della
vita (Famiglia, Figli, Amici, Soldi, Carriera, Tempo libero) ognuno risponde su otto voci, senza
vedere le scelte dell'altro. Solo alla fine compare la mappa condivisa.

**Avvio:** apri `la-nostra-mappa/index.html` in un browser. Nessuna installazione, nessun server,
nessuna rete: lo stato vive solo in memoria e "Ricomincia" lo azzera del tutto.

**Come funzionano le voci**
- Ogni voce ha una scala da 0 a 10 pallini (massimo 10 per voce). I pallini sono un valore concreto:
  per esempio *Vicinanza alle famiglie* va da «Oltre 3 ore di viaggio» (0) a «Nello stesso quartiere» (10).
  Cinque livelli descrivono la scala: 0 · 1–3 · 4–6 · 7–9 · 10.
- Non c'è un limite ai pallini sul totale e si può sempre andare avanti: il segnale sta nelle combinazioni.

**La dashboard finale**: sei riquadri con una barra colorata per area, una sintesi a etichette (allineati,
differenza, da discutere; toccandole si apre la voce), poi la mappa: una riga per voce con i due pallini
su una scala 0–10 e la barra colorata dall'esito. I dettagli si aprono al tocco. In fondo, i segnali
da tenere d'occhio e la domanda sul luogo.

**Come si leggono i risultati** (soglie in `T`, funzione `classify`)
- distanza ≤ 2: in sintonia (pilastro condiviso se entrambi ≥ 6); nessuno dei due oltre 2: poco in gioco
- distanza 3–4: sfumatura, ciascuno si sposta al massimo di 2 pallini per incontrarsi
- distanza 5–6: da negoziare
- distanza ≥ 7: punto da discutere (i temi di fondo, `crit`, hanno la precedenza)
- **Dentro ognuno di voi** (`CONFLICTS`, `internalConflicts`): incrocia le risposte della stessa persona.
  *Non coerenti* se si escludono (nessun desiderio di figli ma un numero di figli), *difficili da
  conciliare* se tirano in direzioni opposte (vivere accanto alle famiglie e trasferirsi ovunque),
  più i controlli «il tempo/il budget non basta per tutto» e le aree con molte voci al massimo.
- **Dove le scelte si incrociano** (`crossings`): combinazioni tra voi due che si rinforzano
  (es. radici condivise) o mettono in tensione (es. uno vuole restare vicino alle famiglie, l'altro
  spostarsi per lavoro).
- **Requisiti del luogo** (`placeNeeds`): cosa dovrebbe permettere il luogo, senza scegliere una città.

**Personalizzazione:** in cima allo `<script>` ci sono `MAX_PER_ITEM`, `AREAS` (aree, voci, domanda e
cinque livelli di scala) e le soglie `T`. I nomi si inseriscono nella schermata iniziale.
