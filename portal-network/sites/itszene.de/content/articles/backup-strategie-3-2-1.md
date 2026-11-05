---
title: Backup-Strategie 3-2-1: So sichern KMU ihre Daten gegen Ausfall und Ransomware
slug: backup-strategie-3-2-1
status: draft
kind: ratgeber
ressort: ratgeber
teaser: Drei Kopien, zwei Medien, eine außer Haus – und mindestens eine, die Angreifer nicht erreichen. Wie die 3-2-1-Regel funktioniert und warum erst der Wiederherstellungstest zählt.
author: Redaktion ITSZENE
date: 2026-11-02
tags: [Backup, Ransomware, IT-Sicherheit, Notfallvorsorge]
needs_fact_check: false
sources:
  - "BSI – Datensicherung und IT-Grundschutz | https://www.bsi.bund.de/"
---
Ein defekter Server, ein versehentlich gelöschter Ordner, ein Brand im Büro oder ein Verschlüsselungstrojaner: Es gibt viele Wege, wichtige Daten zu verlieren. Eine durchdachte Datensicherung entscheidet dann darüber, ob ein Unternehmen nach Stunden wieder arbeitet – oder nach Wochen. Die 3-2-1-Regel ist dafür seit Jahren der bewährte Ausgangspunkt.

## Die 3-2-1-Regel

- **3 Kopien** der Daten: das Original und zwei Sicherungen.
- **2 unterschiedliche Speichermedien oder -systeme:** zum Beispiel ein lokales Sicherungsgerät und ein Cloud-Speicher. So führt ein einzelner Fehler – etwa ein defektes Speichersystem – nicht zum Totalverlust.
- **1 Kopie außer Haus:** räumlich getrennt, damit Brand, Wasser oder Diebstahl am Standort nicht alle Kopien gleichzeitig treffen.

## Die Erweiterung: 3-2-1-1-0

Moderne Erpressungssoftware sucht gezielt nach Sicherungen, um sie zu verschlüsseln oder zu löschen. Deshalb hat sich eine Erweiterung etabliert:

- **1 Kopie offline oder unveränderbar:** Eine Sicherung, die vom Netzwerk getrennt ist (etwa ein Wechselmedium, das nach der Sicherung abgezogen wird) oder für einen festgelegten Zeitraum nicht verändert werden kann („immutable“). Viele Speicherlösungen und Cloud-Dienste bieten dafür Funktionen wie Objektsperren.
- **0 Fehler bei der Wiederherstellung:** Sicherungen werden regelmäßig getestet, und zwar durch tatsächliches Zurückspielen.

## Was gesichert werden muss

Häufig werden nur Dateiablagen gesichert – und anderes vergessen. Eine vollständige Liste umfasst:

- Dateiserver und Ablagen, auch in Cloud-Speichern,
- Datenbanken und Fachanwendungen (Buchhaltung, Warenwirtschaft, Branchensoftware),
- E-Mail-Postfächer, auch bei Cloud-Diensten – deren Anbieter sichern meist die Verfügbarkeit des Dienstes, nicht zwingend jeden einzelnen gelöschten Inhalt über lange Zeit,
- Konfigurationen von Servern, Firewalls und Netzwerkgeräten,
- virtuelle Maschinen als Ganzes, um schnell wieder starten zu können,
- Dokumentation, Zugangsdaten für den Notfall und Lizenzinformationen – sicher verwahrt.

## Zwei Kennzahlen, die jede Firma kennen sollte

**RPO (Recovery Point Objective):** Wie viel Datenverlust ist verkraftbar? Wer einmal nachts sichert, verliert im schlimmsten Fall die Arbeit eines Tages. Für manche Systeme ist das zu viel.

**RTO (Recovery Time Objective):** Wie lange darf die Wiederherstellung dauern? Ein großes Backup aus der Cloud zurückzuladen kann je nach Datenmenge und Leitung lange dauern. Wer kurze Ausfallzeiten braucht, benötigt zusätzlich lokale Sicherungen oder Möglichkeiten, Systeme direkt aus der Sicherung zu starten.

Beide Werte sollten mit der Geschäftsleitung festgelegt werden – sie sind eine geschäftliche Entscheidung, keine rein technische.

## Wiederherstellung testen

Eine Sicherung, die nie zurückgespielt wurde, ist eine Hoffnung, kein Backup. Bewährt hat sich:

- **regelmäßige Stichproben:** einzelne Dateien und Postfächer wiederherstellen,
- **in größeren Abständen Komplett-Tests:** ein ganzes System in einer Testumgebung wiederherstellen und die Zeit messen,
- **Protokoll führen:** Was wurde getestet, wie lange hat es gedauert, was ist schiefgegangen?

## Sicherungen schützen

- **Eigene Zugangsdaten** für das Backup-System, getrennt von der normalen Benutzerverwaltung, mit Multi-Faktor-Authentifizierung.
- **Verschlüsselung** der Sicherungen, besonders außer Haus und in der Cloud. Den Schlüssel sicher und getrennt aufbewahren – ohne ihn ist die Sicherung wertlos.
- **Überwachung:** Fehlgeschlagene Sicherungen müssen auffallen. Eine tägliche Statusmeldung, die niemand liest, hilft nicht.
- **Aufbewahrungsfristen** so wählen, dass auch ältere Stände verfügbar sind. Angriffe werden manchmal erst nach Wochen bemerkt.

## Organisatorisches

Wer ist für die Sicherung zuständig, wer prüft sie, und wer entscheidet im Notfall, welche Systeme zuerst wiederhergestellt werden? Diese Fragen gehören in einen schriftlichen Notfallplan. Arbeitet ein Unternehmen mit einem IT-Dienstleister, sollten Umfang, Testintervalle und Wiederherstellungszeiten vertraglich festgehalten werden.

## Kurz-Checkliste

- Sind alle wichtigen Systeme und Cloud-Dienste erfasst?
- Gibt es mindestens eine Kopie außer Haus und eine offline oder unveränderbar?
- Sind RPO und RTO festgelegt?
- Wann wurde zuletzt eine vollständige Wiederherstellung getestet?
- Ist das Backup-System mit eigenen, starken Zugangsdaten geschützt?
- Weiß im Notfall jemand außer der zuständigen Person, wie die Wiederherstellung funktioniert?

Wer diese Fragen mit Ja beantworten kann, ist für die meisten Ausfälle gut gerüstet.
