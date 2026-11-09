---
title: Multi-Faktor-Authentifizierung einführen: Der wirksamste Schutz für Zugänge
slug: mfa-zwei-faktor
status: draft
kind: ratgeber
ressort: ratgeber
teaser: Gestohlene Passwörter sind ein Haupteinfallstor für Angreifer. Welche zweiten Faktoren es gibt, wie sicher sie sind und wie die Einführung im Unternehmen gelingt.
author: Redaktion ITSZENE
date: 2026-11-02
tags: [MFA, Passkeys, IT-Sicherheit, Zugangsschutz]
needs_fact_check: false
sources:
  - "BSI – Zwei-Faktor-Authentisierung | https://www.bsi.bund.de/"
  - "FIDO Alliance – Passkeys | https://fidoalliance.org/"
---
Ein Passwort allein schützt heute nicht mehr zuverlässig. Passwörter werden durch Phishing abgegriffen, bei Datenlecks anderer Dienste erbeutet oder schlicht erraten. Die Multi-Faktor-Authentifizierung (MFA), oft auch Zwei-Faktor-Authentifizierung genannt, ergänzt das Passwort um einen weiteren Nachweis. Sie gilt als eine der wirksamsten und zugleich günstigsten Sicherheitsmaßnahmen.

## Das Prinzip

Bei der Anmeldung werden Nachweise aus mindestens zwei verschiedenen Kategorien verlangt:

- **Wissen:** etwas, das man weiß – etwa ein Passwort oder eine PIN,
- **Besitz:** etwas, das man hat – etwa ein Smartphone oder ein Sicherheitsschlüssel,
- **Inhärenz:** etwas, das man ist – etwa ein Fingerabdruck.

Erbeutet ein Angreifer das Passwort, fehlt ihm der zweite Faktor.

## Die gängigen Verfahren im Vergleich

**SMS-Codes:** weit verbreitet und besser als kein zweiter Faktor. Sie sind aber anfällig, etwa wenn Angreifer eine Rufnummer auf eine eigene SIM-Karte übertragen lassen oder Codes per Phishing abfragen.

**Einmalcodes aus Authenticator-Apps (TOTP):** Eine App erzeugt alle paar Sekunden einen neuen Code. Das ist sicherer als SMS, aber ein geschickt gemachtes Phishing kann auch diese Codes in Echtzeit abgreifen.

**Push-Bestätigung:** Eine App fragt „Anmeldung bestätigen?“. Bequem, aber anfällig für „MFA-Fatigue“: Angreifer lösen so lange Anfragen aus, bis jemand genervt zustimmt. Abhilfe schafft eine Zahlenabfrage, bei der eine auf dem Bildschirm angezeigte Zahl in der App eingegeben werden muss.

**FIDO2-Sicherheitsschlüssel und Passkeys:** Kryptografische Verfahren, bei denen die Anmeldung an die echte Website gebunden ist. Eine gefälschte Seite kann den Nachweis nicht verwenden. Diese Verfahren gelten als **phishing-resistent** und sind für besonders schützenswerte Konten die beste Wahl. Passkeys können auf dem Smartphone, im Betriebssystem oder auf einem Hardware-Schlüssel gespeichert sein.

## Wo MFA zuerst hingehört

Wer nicht alles auf einmal umstellen kann, beginnt mit den Zugängen, deren Missbrauch am meisten Schaden anrichtet:

1. **Administrative Konten** – für Server, Cloud-Verwaltung, Firewall, Backup-System.
2. **E-Mail und Cloud-Dienste** – über das Postfach lassen sich viele andere Passwörter zurücksetzen.
3. **Fernzugänge** – VPN und Remote-Desktop.
4. **Finanzsysteme** – Online-Banking, Buchhaltung, Zahlungsfreigaben.
5. **Zugänge externer Dienstleister**, die in Ihre Systeme kommen.

## Einführung in der Praxis

- **Bestandsaufnahme:** Welche Anwendungen unterstützen MFA, welche zentral über ein Identitätssystem (Single Sign-on)?
- **Verfahren festlegen:** Für Administratoren phishing-resistente Verfahren, für alle anderen mindestens Authenticator-App mit Zahlenabfrage.
- **Kommunizieren:** Mitarbeitende vorab informieren, warum MFA kommt und wie es funktioniert. Eine kurze Anleitung mit Bildern spart viele Rückfragen.
- **Schrittweise ausrollen:** zunächst eine Pilotgruppe, dann abteilungsweise.
- **Wiederherstellung regeln:** Was passiert, wenn ein Smartphone verloren geht? Ersatzcodes sicher verwahren, einen geprüften Prozess für das Zurücksetzen festlegen – und dabei die Identität der anfragenden Person sorgfältig prüfen, denn genau hier setzen Betrüger an.
- **Ausnahmen begrenzen:** Alte Anmeldeverfahren, die MFA umgehen, abschalten. Notfallkonten ohne MFA nur in kleiner Zahl, mit sehr langen Passwörtern, sicher verwahrt und überwacht.

## Häufige Einwände

**„Das ist zu umständlich.“** Moderne Verfahren wie Passkeys sind oft bequemer als Passwörter. Zudem lässt sich einstellen, dass bei vertrauenswürdigen Geräten nicht bei jeder Anmeldung ein zweiter Faktor nötig ist.

**„Wir sind doch kein Ziel.“** Viele Angriffe laufen automatisiert und wahllos. Gestohlene Zugangsdaten werden massenhaft durchprobiert – unabhängig von der Unternehmensgröße.

**„Mitarbeitende wollen ihr privates Handy nicht nutzen.“** Dann sind Hardware-Schlüssel oder dienstliche Geräte eine gute Alternative.

## MFA für Dienstleister und gemeinsam genutzte Konten

Zwei Bereiche werden bei der Einführung oft übersehen. Erstens: Zugänge externer Dienstleister. Wer per Fernwartung oder über Verwaltungsportale auf Ihre Systeme zugreift, sollte ebenfalls einen zweiten Faktor nutzen – idealerweise mit persönlichen Konten statt eines gemeinsamen Dienstleister-Logins. Lassen Sie sich das vertraglich zusichern. Zweitens: gemeinsam genutzte Konten, etwa für Social-Media-Profile, Bankportale oder Lieferantenportale. Hier helfen Passwortmanager für Teams, die Zugangsdaten und Einmalcodes sicher teilen, oder – wo möglich – die Umstellung auf persönliche Konten mit Rollen. Dokumentieren Sie, welche Konten es gibt, wer Zugriff hat und wie MFA dort eingerichtet ist, damit beim Ausscheiden von Mitarbeitenden nichts vergessen wird.

## Fazit

MFA verhindert einen Großteil der Angriffe, die auf gestohlenen Passwörtern beruhen. Wer bei Administratoren, E-Mail und Fernzugängen beginnt, phishing-resistente Verfahren bevorzugt und die Wiederherstellung sauber regelt, erhöht die Sicherheit mit überschaubarem Aufwand deutlich.
