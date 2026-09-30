# Giochi

## La nostra mappa

Gioco da tavolo digitale per due persone sullo stesso dispositivo. In ciascuna delle sei aree della
vita (Famiglia, Figli, Amici, Soldi, Carriera, Tempo libero) ognuno distribuisce 20 pallini su otto
voci, senza vedere le scelte dell'altro. Solo alla fine compare la mappa condivisa.

**Avvio:** apri `la-nostra-mappa/index.html` in un browser. Nessuna installazione, nessun server,
nessuna rete: lo stato vive solo in memoria e "Ricomincia" lo azzera del tutto.

**Come funzionano le voci**
- Ogni voce ha una scala da 0 a 10 pallini (massimo 10 per voce). I pallini sono un valore concreto:
  per esempio *Vicinanza alle famiglie* va da «Oltre 3 ore di viaggio» (0) a «Nello stesso quartiere» (10).
  Cinque livelli descrivono la scala: 0 · 1–3 · 4–6 · 7–9 · 10.
- I pallini sono un budget (20 per area): non si può avere tutto al massimo.

**Come si leggono i risultati** (soglie in `T`, funzione `classify`)
- distanza ≤ 2: in sintonia (pilastro condiviso se entrambi ≥ 6); nessuno dei due oltre 2: poco in gioco
- distanza 3–4: sfumatura, ciascuno si sposta al massimo di 2 pallini per incontrarsi
- distanza 5–6: da negoziare
- distanza ≥ 7: punto da discutere (i temi di fondo, `crit`, hanno la precedenza)
- **Incroci** (`crossings`): combinazioni di voci diverse che si rinforzano (es. radici condivise) o
  vanno messe in relazione (es. vicinanza alle famiglie × spostarsi per lavoro).
- **Requisiti del luogo** (`placeNeeds`): cosa dovrebbe permettere il luogo, senza scegliere una città.

**Personalizzazione:** in cima allo `<script>` ci sono `POINTS`, `MAX_PER_ITEM`, `AREAS` (aree, voci,
definizione e cinque livelli di scala) e le soglie `T`. I nomi si inseriscono nella schermata iniziale.
