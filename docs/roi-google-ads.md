# ROI: Google Ads on the MERKANT Medien Portal Network

**Status:** November 2026 · Model: `docs/roi_model.py` (re-run with your own numbers)
**Scope:** Revenue from **Google ads only** (AdSense, later Google Ad Manager) across all portals: firmennachrichten.de, itszene.de, it-erfahrungen.de and later systemhauserfahrungen.de, agenturerfahrungen.de, firmenkoepfe.de.
Other revenue (paid review packages, sponsored content, leads, newsletter) is **not** included. Google ads alone are the most conservative way to look at the project.

> All figures are planning assumptions, not forecasts. Real RPM and traffic are only known after 2–3 months live. Replace the assumptions with your real AdSense numbers as soon as you have them.

---

## 1. How the revenue works

```
Ad revenue / month = Page views / 1,000 × Page RPM
```

- **Page RPM** = what you earn per 1,000 page views, already after Google's share (publishers keep about 80 % for AdSense display ads).
- **Typical page RPM in Germany (AdSense, 2025/26, rough ranges):**
  - general news: €1.50–4
  - business/B2B news: €3–8
  - IT/software/B2B services (high advertiser bids): €5–15
  - review/comparison pages with buying intent: €4–12
- **Consent effect (DSGVO/TTDSG):** Only visitors who accept the consent banner get personalised ads. Typically 50–75 % accept. Non-consented visitors earn noticeably less. The RPMs in the scenarios already include this.
- **Ad layout:** 3–4 ad slots per article page is normal. More slots raise RPM briefly but hurt speed, SEO and reader trust.

---

## 2. Cost basis (from the concept, base case)

| One-off (Phase 0–1) | € |
|---|---|
| Raspberry Pi 5 + NVMe + UPS | 300 |
| 22 domains (first year) | 200 |
| Legal setup (imprint, privacy, terms, editorial statute, review rules) | 7,500 |
| Trademark search & filing (MERKANT Medien + logo) | 1,000 |
| Freelance development support (you build most yourself) | 3,000 |
| **Total one-off** | **12,000** |

| Monthly running | € |
|---|---|
| LLM API (drafts + fact check, 40–60 texts/day) | 100 |
| Company data / register API | 300 |
| Lawyer retainer | 300 |
| Media liability insurance | 150 |
| Cloudflare, backup, newsletter, consent tool, misc. | 50 |
| **Total monthly** | **900** |

Your own time (about 1–1.5 h/day for approvals plus setup) is **not** priced in.

---

## 3. Scenarios (24 months)

Traffic = page views per month across all portals. Growth follows a typical ramp for a new news site: slow Google trust in months 1–6, then Google News/Discover takes over.

| Scenario | Month 1 | Month 12 | Month 24 | Page RPM |
|---|---|---|---|---|
| Conservative | 5,000 | 150,000 | 400,000 | €3 |
| **Base** | 10,000 | 400,000 | 1,200,000 | **€5** |
| Optimistic | 20,000 | 1,000,000 | 3,000,000 | €8 |

### 3.1 Results

| | Conservative | **Base** | Optimistic |
|---|---|---|---|
| Ad revenue month 12 | €450 | **€2,000** | €8,000 |
| Ad revenue month 24 | €1,200 | **€6,000** | €24,000 |
| Monthly costs covered from | month 21 | **month 10** | month 6 |
| Full payback incl. one-off | after month 24 | **month 20** | month 12 |
| Revenue in 24 months | €11,200 | **€52,600** | €209,200 |
| Total cost in 24 months | €33,600 | **€33,600** | €33,600 |
| Net result after 24 months | −€22,400 | **+€19,000** | +€175,600 |
| **ROI after 12 months** | −93 % | **−70 %** | +16 % |
| **ROI after 24 months** | −67 % | **+57 %** | +523 % |

*ROI = (cumulative revenue − cumulative cost) / cumulative cost.*

### 3.2 Month by month (base case)

| Month | Page views | Ad revenue | Profit/month | Cumulative |
|---|---|---|---|---|
| 1 | 10,000 | €50 | −€850 | −€12,850 |
| 3 | 19,600 | €98 | −€802 | −€14,482 |
| 6 | 53,500 | €267 | −€633 | −€16,587 |
| 9 | 146,300 | €731 | −€169 | −€17,659 |
| 12 | 400,000 | €2,000 | +€1,100 | −€15,906 |
| 18 | 692,800 | €3,464 | +€2,564 | −€4,570 |
| 24 | 1,200,000 | €6,000 | +€5,100 | **+€19,016** |

### 3.3 The one number to watch: break-even traffic

Page views per month needed to cover the €900 running costs:

| Page RPM | Page views needed / month |
|---|---|
| €2 | 450,000 |
| €3 | 300,000 |
| €5 | 180,000 |
| €8 | 112,500 |
| €12 | 75,000 |

**Takeaway:** Once real RPM is known (after ~60 days), this table tells you exactly how much traffic you need.

---

## 4. What drives the result (in order of impact)

1. **Traffic from Google News & Discover:** Discover alone can multiply page views. Getting into Google News and producing reliable, fast company news is the biggest lever.
2. **Topic mix with high RPM:** IT, software, security and B2B services pay 2–3× more per page than general news. ITSZENE and IT-ERFAHRUNGEN lift the blended RPM.
3. **Consent rate:** A well-designed, compliant consent banner with a Google-certified CMP (TCF 2.2) can lift accept rates from ~50 % to ~70 %.
4. **Page speed & layout:** Static pages via Cloudflare are fast. Use lazy-loaded ads and fixed slot sizes to avoid layout shift.
5. **Switch to Google Ad Manager + header bidding** (from ~1M page views/month): typically +20–50 % RPM versus pure AdSense.

**Honest assessment:** Google ads alone only pay off with real traffic (base case or better). That is why the concept combines ads with paid review packages, sponsored content and leads. Those can be profitable at much lower traffic.

---

## 5. Step-by-step execution plan

### Phase A: Prepare (weeks 1–2)
1. **Register domains** from the purchase list (concept section 2.2), at minimum `merkant-medien.de`, `firmennachrichten.de`, `itszene.de`, `it-erfahrungen.de`.
2. **Set up the operator:** company (GmbH/UG) or sole trader, business bank account. AdSense pays out to the account holder, so the account must be in the operator's name.
3. **Tax:** ad revenue is business income. Register the business, get a VAT ID (USt-IdNr.). Google Ireland invoices under reverse charge.
4. **Legal pages per site:** imprint (with § 18 (2) MStV responsible person), privacy policy (naming Google AdSense/Ad Manager, cookies, consent), terms, editorial guidelines, contact.

### Phase B: Build sites that AdSense will approve (weeks 2–8)
5. **Launch each site with real substance before applying:** at least 30–50 published, human-approved articles per site, clear navigation, About page, author page, contact page.
   AdSense regularly rejects new sites for "low value content". Thin, mass-generated pages are the most common rejection reason.
6. **Technical basics:** HTTPS (Cloudflare), XML sitemap, Google Search Console verified for each domain, fast mobile pages, no broken links.
7. **Consent management:** Install a **Google-certified CMP supporting TCF 2.2**. This is mandatory for serving Google ads in the EEA. Options: Google's own "Privacy & messaging" in AdSense (free), or e.g. Usercentrics, Sourcepoint, consentmanager.
8. **Plan ad slots in the templates:** fixed placeholders (e.g. 1 below the lead paragraph, 1–2 in the text, 1 in the sidebar/footer), reserved heights to avoid layout shift. Keep editorial content and ads clearly separated and labelled "Anzeige".

### Phase C: Apply for AdSense (weeks 6–10)
9. **Create one AdSense account** for the operator (one account per person/company. Never create several).
10. **Add each domain as a separate site** in AdSense → Sites. Each site is reviewed individually. Start with firmennachrichten.de, then add the others once they have enough content.
11. **Add `ads.txt`** to every domain root with the line AdSense shows you (`google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`). Your static builder can generate it for all sites.
12. **Insert the AdSense code** in the site template `<head>` and wait for review (usually days to a few weeks).
13. **If rejected:** read the reason, add more substantial content, fix navigation/policy pages, re-apply after 2–4 weeks.

### Phase D: Go live & measure (months 2–4)
14. **Start with manual ad units** in your reserved slots (more control than Auto ads), or test Auto ads on one site for comparison.
15. **Connect AdSense with Google Analytics 4 / Search Console** (or keep Plausible for traffic and use AdSense reports for revenue).
16. **Weekly check (15 min):** page views, page RPM per site, consent rate, Core Web Vitals, policy center warnings.
17. **After 60 days:** put your real RPM per site into `docs/roi_model.py` and re-run it. Decide which portal gets more content.

### Phase E: Grow revenue (months 4–12)
18. **Google News & Discover:** apply in Google Publisher Center, use large images (≥1,200 px), clear headlines, publish fast.
19. **Optimise the topic mix:** more IT/security/software content (higher RPM), evergreen guides that rank permanently.
20. **A/B test ad layout:** one change at a time, measure RPM *and* time on page. Remove slots that hurt reading.
21. **Diversify:** turn on review packages, sponsored content (labelled) and newsletter sponsoring. Don't depend on Google alone.

### Phase F: Scale (from ~1M page views/month)
22. **Move to Google Ad Manager** with header bidding (e.g. Prebid) or a certified partner/marketer for better prices.
23. **Direct sales:** sell premium placements to IT vendors and service providers (often several times the programmatic price).

### Rules you must never break (account ban risk)
- ❌ Never click your own ads, never ask anyone to click ads.
- ❌ Never buy cheap traffic (bots, traffic exchanges, pop-under traffic) to inflate page views.
- ❌ No ads on pages without substantial content (empty company profiles, tag pages, thin auto-pages).
- ❌ No misleading ad placement (ads that look like navigation or article links).
- ❌ Don't place AdSense code on pages that violate content policies (e.g. unverified allegations).

A banned AdSense account usually cannot be restored and affects all your domains at once.

---

## 6. Decision checkpoints

| When | Check | Decision |
|---|---|---|
| Month 3 | AdSense approved for ≥ 2 sites? RPM known? | If not approved: improve content before investing more |
| Month 6 | Page views ≥ 50,000/month? | Below: focus on Google News/Discover and the best-performing portal |
| Month 12 | Ad revenue ≥ €900/month (running costs covered)? | Below: add paid review packages/sponsoring before adding new portals |
| Month 18 | Page views ≥ 700,000/month? | Above: evaluate Ad Manager + header bidding and a move from Pi to cloud server |

---

## 7. Operating entity: futureconceptions UG (haftungsbeschränkt) i.G.

The portals are run by **futureconceptions UG (haftungsbeschränkt)**, currently **in formation (i.G.)**. MERKANT Medien is used as a brand of the UG.
*Not legal or tax advice. Confirm with notary and tax advisor.*

### 7.1 What "i.G." means for the plan
| Stage | Liability | What you may do |
|---|---|---|
| **Before notarisation** (pre-formation) | Founders liable **personally and without limit** (treated like a partnership/sole trader) | Planning, building the software, writing unpublished drafts |
| **Notarised, not yet registered** (UG i.G.) | Anyone acting in the UG's name is **personally liable** (§ 11 (2) GmbHG); founders liable for losses | Preparation, contracts clearly marked "i.G.", bank account opening |
| **Registered in the commercial register** | Liability limited to the UG's assets | **Go live**, apply for AdSense, publish news and reviews |

**Rule:** No portal goes live and no AdSense application before the UG is registered. Publishing company news and reviews carries legal risk that must not hit you personally.

### 7.2 Do now, while the UG is still in formation
1. **Business purpose (Unternehmensgegenstand):** add media activities *before* registration. That saves a later notarised amendment. Suggested wording for the notary:
   *„Betrieb von Online-Medien, Nachrichten-, Informations- und Bewertungsportalen, Erstellung und Verbreitung redaktioneller Inhalte, Vermarktung von Werbeflächen sowie Entwicklung und Betrieb von Software und digitalen Dienstleistungen.“*
2. **Domains:** register now so they aren't lost, either in the founder's name with a documented later transfer to the UG (holder change at the registrar), or directly in the name „futureconceptions UG (haftungsbeschränkt) i.G.“ if the registrar accepts it. Transfer all domains to the UG right after registration.
3. **Collect all invoices in the UG's name** („futureconceptions UG (haftungsbeschränkt) i.G.“) so that formation-phase costs can be booked in the UG. Agree with the tax advisor which costs before notarisation the UG takes over.
4. **Funding:** the one-off costs (~€12,000) will likely exceed the share capital. Plan a **shareholder loan** (written agreement, ideally with subordination/Rangrücktritt so the UG isn't over-indebted) or a higher capital contribution.
5. **Insurance:** request quotes for media liability insurance now; start cover on the go-live date.

### 7.3 Right after registration
1. Business bank account in the UG's name (if not opened already), business registration (Gewerbeanmeldung), tax registration (Fragebogen zur steuerlichen Erfassung), VAT ID.
2. Transfer domains to the UG. Trademark filings in the UG's name.
3. Imprint on all portals: „MERKANT Medien – eine Marke der futureconceptions UG (haftungsbeschränkt)“, registered office, register court, HRB number, managing director, responsible person under § 18 (2) MStV.
4. **Create the AdSense account as a business account in the UG's name.** The payee name must match the UG's bank account. An individual AdSense account can't be converted later.
5. Only then: go live and apply for AdSense (Phase C of the plan).

### 7.4 Effect on the ROI
- **No tax offset in year 1:** a new UG has no other profits yet, so the portal losses (base case about −€16,000 after 12 months) become a **loss carryforward**. It reduces tax once the UG earns money (portals or other business) and has full value later, but brings no cash benefit immediately. The ROI figures above (before tax) therefore stay unchanged.
- **Reserve rule:** a UG must retain 25 % of annual profit until its capital reaches €25,000. That limits payouts, not ROI.
- **Timeline:** registration usually takes 1–4 weeks after notarisation. It fits into Phase A/B (weeks 1–8): build the sites while the registration runs, then apply for AdSense in weeks 6–10.

