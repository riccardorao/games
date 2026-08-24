# Sacchi e Picche — segnapunti per Spades

Pagina singola e autonoma (`spades/index.html`): nessun server, nessuna installazione, nessun
account. Si apre con un doppio clic e funziona anche offline. Tutti i dati restano nella memoria
del browser di chi la apre.

## Come si usa

1. Apri `spades/index.html` nel browser.
2. Alla prima apertura scegli **modalità**, **nomi**, punteggio obiettivo e prese per mano.
3. Per ogni mano inserisci, per ciascun giocatore, la **dichiarazione** e le **prese fatte**
   (tasti +/−, oppure digita il numero; frecce su/giù e Invio per passare al campo successivo).
   Il Nil si segna con i pulsanti `Nil` e `Buio`.
4. Quando la somma delle prese arriva al totale della mano il pulsante **Registra mano** si sblocca.
   L'anteprima mostra il punteggio prima di confermare.

Ogni mano registrata resta nel **Registro** e si può modificare o eliminare: punteggi, sacchi e
penalità vengono ricalcolati da capo sull'intera partita.

## Punteggio

Regole standard, tutte modificabili dal pannello **Regole**:

| Voce | Predefinito |
| --- | --- |
| Presa dichiarata | 10 punti (in negativo se il contratto non si chiude) |
| Presa in più (sacco) | 1 punto |
| Sacchi accumulati | penalità di 100 punti ogni 10 sacchi, il contatore riparte dal resto |
| Nil | +100 se riuscito, −100 se fallito |
| Nil al buio | +200 / −200 |
| Nil fallito | le prese diventano sacchi della squadra e non contano per il contratto del compagno |

Modalità disponibili: **a coppie** (1° con 3° giocatore, 2° con 4°) e **individuale** con 3, 4 o 5
giocatori, ognuno con contratto e sacchi propri.

## Salvare e spostare una partita

La sessione si salva da sola nel browser. Il pulsante **Backup** mostra il testo completo della
partita: si copia per conservarla, oppure si incolla un backup precedente e si preme **Carica**
per riprenderla su un altro dispositivo o browser.

**Azzera** cancella solo le mani giocate: nomi, squadre e regole restano.
