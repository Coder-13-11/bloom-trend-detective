# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primary (confirmed by the user, 2026-11-15):** lake managers and agency or academic scientists who use satellite bloom indicators and need to know whether a trend is in the lake or in the instrument. They read numbers, intervals and methods, and distrust claims without them.
- **Secondary:** NASA Space Apps judges assessing the project; students and residents checking their own lake (the challenge's stated audience).

## Product Purpose
Bloom Trend Detective cross-examines the satellite cyanobacteria-bloom record for 121 Florida lakes against independent field chlorophyll samples. For any lake and variable it reports a rate of change, a significance test and a plain verdict, plus a "second opinion" from the field record. Success: a manager can decide in under a minute whether a satellite trend for their lake is corroborated, and see the evidence.

## Positioning
Every result is checked against an independent record and was computed under rules written down beforehand. A satellite-only trend viewer cannot truthfully claim that.

## Operating Context
- Static site on GitHub Pages; no server, no login; one precomputed JSON file (about 1.1 MB).
- Used on desktop by analysts; opened on phones by judges and the public.
- Evaluated tonight (Space Apps deadline 2026-11-15 23:59 local) from the project page link.

## Capabilities and Constraints
- Variables: satellite bloom weeks, satellite bloom extent (CyAN, 2020–2026), field chlorophyll (Water Quality Portal, 2000–2025), NASA MERRA-2 warm-season air temperature and rainfall (1981–2025).
- Per-lake trend: Sen's slope, Mann-Kendall p, Benjamini–Hochberg adjustment, verdict wording fixed in the protocol.
- Statewide cross-examination: field vs satellite 2020–2025, drift test, field-truth forecast test.
- All numbers on the page come from `site/data/site.json`; nothing may be typed in by hand.
- Claims that must never appear: toxin, health or water-safety guidance; dollar savings; causes of the trend; "first"; that the instrument drifted (it is one of three suspects); that EPA's model is wrong.
- Verdict wording, interval notation and the exploratory/confirmatory labels are fixed by `research/protocol.md`.

## Brand Commitments
- Name: "Bloom Trend Detective: Florida Lakes". The detective framing (witnesses, cross-examination, suspects) is established copy.
- No team or member names on the site or slides (confirmed by the user).
- No filler, padding or generic template look (confirmed by the user: "no filler or AI slop").
- AI-assistance disclosure must stay visible.

## Evidence on Hand
- `site/data/site.json`: 121 lakes with series, trends, cross-check, drift effects, forecast metrics.
- One NASA MODIS Terra true-colour image of Lake Okeechobee (20 June 2023), `site/img/`.
- 7-slide deck generated from `site/slides.html`.
- No logo, no photography beyond the MODIS image, no testimonials, no user research. None may be invented.

## Product Principles
1. Evidence before assertion: every claim sits next to its number, interval and sample size.
2. Say what is not known as plainly as what is.
3. One lake, one question, one screen: the lake view answers "is it real?" without scrolling through narrative.
4. The same page must serve a scientist's scrutiny and a newcomer's first minute.

## Accessibility & Inclusion
- Colour is never the only carrier of a verdict; text labels accompany every colour.
- Works from 360 px wide; keyboard reachable; respects reduced motion and light/dark preference.
