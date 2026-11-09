---
title: Score-Methodik
description: So berechnet ${site_name} den Score eines Unternehmens – gewichteter Mittelwert, Aktualität, Bayes-Glättung. Zahlung hat keinen Einfluss.
---
Der Score fasst die Bewertungen eines Unternehmens in einer Zahl zwischen 1 und 5 zusammen. Wir legen die Berechnung vollständig offen.

## Die Regeln

1. **Gewichteter Mittelwert:** Der Score ist der gewichtete Durchschnitt der Gesamtnoten (1 bis 5 Sterne) aller veröffentlichten Bewertungen.
2. **Aktualität:** Neuere Bewertungen zählen stärker. Das Gewicht einer Bewertung halbiert sich alle ${score_half_life} Monate (Halbwertszeit). Eine 12 Monate alte Bewertung zählt also halb so viel wie eine heutige – sie verschwindet aber nicht.
3. **Herkunft:** Verifizierte Bewertungen erhalten das Gewicht ${weight_verified}, eingeladene ${weight_invited}, organische ${weight_organic}.
4. **Bayes-Glättung:** Profile mit wenigen Bewertungen starten bei einem neutralen Ausgangswert von ${score_prior_mean} Sternen. Dieser Ausgangswert zählt so viel wie ${score_prior_weight} aktuelle Bewertungen. Mit jeder weiteren Bewertung nähert sich der Score dem tatsächlichen Durchschnitt an. So kann eine einzelne sehr gute oder sehr schlechte Bewertung den Score nicht dominieren.
5. **Teilkriterien:** Für jedes Teilkriterium zeigen wir den gewichteten Durchschnitt (Aktualität × Herkunft) der abgegebenen Teilnoten – ohne Glättung.

## Die Formel

Für jede Bewertung *i* mit Note *n* und Alter *t* (in Monaten):

`Gewicht = 0,5 ^ (t / ${score_half_life}) × Herkunftsgewicht`

`Score = (${score_prior_weight} × ${score_prior_mean} + Summe(Gewicht × n)) / (${score_prior_weight} + Summe(Gewicht))`

Der Score wird auf eine Nachkommastelle gerundet. Er wird bei jeder neuen Bewertung und regelmäßig wegen der Alterung neu berechnet.

## Was keinen Einfluss hat

- **Zahlung:** Bezahlpakete beeinflussen weder Score noch Sortierung noch Sichtbarkeit von Bewertungen.
- **Antworten des Unternehmens** verändern den Score nicht.
- **Werbung:** Anzeigen auf dem Portal sind als „Anzeige“ gekennzeichnet und haben keinen Bezug zu Score oder Sortierung.

## Sortierung in Kategorien

In Kategorie- und Ortslisten sortieren wir nach Score, bei Gleichstand alphabetisch. Bezahlte Platzierungen gibt es in diesen Listen nicht. Sollten wir künftig bezahlte Einblendungen anbieten, sind sie deutlich als „Anzeige“ gekennzeichnet und vom Ranking getrennt.

## Indexierung

Firmenprofile ohne Bewertung werden zwar angezeigt, aber erst ab der ersten veröffentlichten Bewertung für Suchmaschinen freigegeben.
