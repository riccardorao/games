# Segnapicche

Segnapunti per il gioco di carte di picche (Spades), in una pagina sola: `index.html`.
Nessun server, nessuna installazione, funziona anche offline. I punteggi restano nel browser
di chi apre la pagina.

## Uso

1. Apri `index.html`.
2. Al primo avvio: nomi, modalita' (a coppie o individuale a 3-5), obiettivo e prese per mano.
3. Per ogni mano scrivi dichiarazione e prese di ciascun giocatore (tasti +/-, digitazione,
   frecce su/giu', Invio per il campo successivo). Il tasto `nil` cicla su Nil e Nil al buio.
4. Quando le prese quadrano, **Registra**.

Nel registro, tocca una riga per correggerla e la × per eliminarla: sacchi e penalita' vengono
ricalcolati su tutta la partita.

## Punteggio

Valori standard, modificabili dal menu ... → Regole:

| Voce | Default |
| --- | --- |
| Presa dichiarata | 10 pt (in negativo se il contratto non chiude) |
| Sacco | 1 pt, penalita' 100 ogni 10 sacchi |
| Nil | ±100, al buio ±200 |

## Menu ...

Giocatori e partita, Regole, Backup (copia/incolla la partita come testo per spostarla altrove),
Annulla ultima mano, Azzera registro (cancella solo le mani).
