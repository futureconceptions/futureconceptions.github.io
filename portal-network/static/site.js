/* MERKANT Medien – kleines Seiten-Script (kein Framework, keine externen Abhängigkeiten).
   1. Reichweitenmessung (selbst gehostet) – lädt erst nach Einwilligung über die TCF-2.2-CMP.
   2. Link "Datenschutzeinstellungen" öffnet die Google-CMP erneut.
   3. Client-seitige Suche über /search-index.json (nur auf /suche/). */
(function () {
  "use strict";
  var body = document.body;

  /* ---------- 1. Analytics nur nach Einwilligung ---------- */
  var aSrc = body.getAttribute("data-analytics-src");
  var aId = body.getAttribute("data-analytics-id");
  var needConsent = body.getAttribute("data-analytics-consent") !== "false";
  var loaded = false;
  function loadAnalytics() {
    if (loaded || !aSrc) return;
    loaded = true;
    var s = document.createElement("script");
    s.defer = true; s.src = aSrc;
    if (aId) s.setAttribute("data-website-id", aId);
    document.head.appendChild(s);
  }
  if (aSrc) {
    if (!needConsent) { loadAnalytics(); }
    else {
      // TCF 2.2: Zweck 1 (Speichern/Zugriff) und Zweck 8 (Messung von Inhalten)
      var tries = 0;
      var wait = setInterval(function () {
        tries++;
        if (typeof window.__tcfapi === "function") {
          clearInterval(wait);
          window.__tcfapi("addEventListener", 2, function (tc, ok) {
            if (!ok || !tc) return;
            if (tc.eventStatus !== "tcloaded" && tc.eventStatus !== "useractioncomplete") return;
            var p = tc.purpose && tc.purpose.consents;
            if (p && p[1] && p[8]) loadAnalytics();
          });
        } else if (tries > 40) { clearInterval(wait); } // ohne CMP: keine Messung
      }, 250);
    }
  }

  /* ---------- 2. Einwilligung widerrufen / ändern ---------- */
  var revoke = document.getElementById("consent-settings");
  if (revoke) {
    revoke.addEventListener("click", function () {
      window.googlefc = window.googlefc || {};
      window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];
      window.googlefc.callbackQueue.push(function () {
        if (window.googlefc.showRevocationMessage) window.googlefc.showRevocationMessage();
      });
    });
  }

  /* ---------- 3. Suche ---------- */
  var form = document.getElementById("search-form");
  var list = document.getElementById("search-results");
  if (!form || !list) return;
  var input = form.querySelector("input[name=q]");
  var status = document.getElementById("search-status");
  var index = null;

  function norm(s) {
    return (s || "").toLowerCase()
      .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss");
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function render(q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    list.innerHTML = "";
    if (!terms.length) { status.textContent = "Bitte einen Suchbegriff eingeben."; return; }
    var hits = index.filter(function (d) {
      var hay = norm(d.title + " " + d.text + " " + (d.section || ""));
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    }).slice(0, 50);
    status.textContent = hits.length ? hits.length + " Treffer für „" + q + "“" : "Keine Treffer für „" + q + "“.";
    hits.forEach(function (d) {
      var li = document.createElement("li");
      li.innerHTML = '<p class="kicker">' + esc(d.section || "") + '</p><a href="' + esc(d.url) + '"><strong>' +
        esc(d.title) + "</strong></a><br><span class=\"meta\">" + esc(d.text.slice(0, 180)) + "</span>";
      list.appendChild(li);
    });
  }
  function run() {
    var q = input.value.trim();
    if (index) { render(q); return; }
    status.textContent = "Suche wird geladen …";
    fetch("/search-index.json").then(function (r) { return r.json(); }).then(function (data) {
      index = data; render(q);
    }).catch(function () { status.textContent = "Die Suche ist gerade nicht verfügbar."; });
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    history.replaceState(null, "", "?q=" + encodeURIComponent(input.value.trim()));
    run();
  });
  var initial = new URLSearchParams(location.search).get("q");
  if (initial) { input.value = initial; run(); }
})();
