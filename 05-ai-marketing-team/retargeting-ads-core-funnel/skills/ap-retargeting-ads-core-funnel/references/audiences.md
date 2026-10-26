# The Four Custom Audiences + Meta Mechanics

These four audiences are the raw material for every retargeting layer. Build all four first; the layers just slice and combine them.

## The four audiences

1. **Video viewers (30 days)** — everyone who watched your organic Instagram/Facebook video content in the last 30 days.
2. **Landing page visitors** — anyone who reached your opt-in page.
3. **Booking page visitors** — anyone who reached your calendar/booking page.
4. **Thank-you page visitors** — anyone who reached the thank-you page (they booked).

Audiences 2, 3, and 4 map exactly to the steps of your funnel: video → landing page → booking page → thank-you page. That order matters — the layers use each stage to exclude the one below it.

## Why the 30-day window matters

The video audience uses a rolling 30-day window. It cleans itself: the moment a viewer passes 31 days without watching again, they drop out of the audience automatically. You never have to prune it. You are always advertising to people who saw you recently, while Instagram and Facebook keep feeding fresh organic viewers in the top.

## Building audience 1 — Video viewers

In Meta Ads Manager, go to **Audiences → Create audience → Custom audience → Video**.

- Choose the engagement level (people who watched a few seconds, or more — start broad).
- Select the Instagram account and/or Facebook Page whose organic videos you want to capture.
- Set the retention window to **30 days**.
- Name it clearly, e.g. `Video viewers — 30d`.

This captures organic viewers, which is the whole point — you are retargeting the attention your content already earned.

## Building audiences 2, 3, 4 — Website visitors by URL path

These three are all the same method: a **website custom audience** matched by the URL path of the page.

Requirements: your Facebook pixel must be installed on your pages so Meta can see the visits.

In Meta Ads Manager: **Audiences → Create audience → Custom audience → Website**.

- Set the rule to **URL contains** and enter the page's path.
- Use the *path* — the part after your domain. If your opt-in page is `yoursite.com/free-guide`, the path is `/free-guide`.
- Set a retention window (30–180 days is typical; longer keeps more people in the pool).
- Name each one clearly: `Landing page visitors`, `Booking page visitors`, `Thank-you page visitors`.

## URL-path hygiene — do not skip this

If you run split tests, your landing page path may have numbered variants like `/opt-in-1` and `/opt-in-2`. If you build the audience on `/opt-in-1`, you only capture people who saw that one version, and your tracking gets messy.

**Fix:** use the universal stem. Match on `/opt-in` (which "contains" catches for both `/opt-in-1` and `/opt-in-2`), or the shared part of the path. This way the audience captures everyone who hit any version of the page, and your testing doesn't fragment the tracking.

Ask the user: "Do you run split tests with numbered page versions like page-1, page-2?" If yes, strip the number and match the shared stem.

## Sanity checks

- Confirm the pixel is actually firing on each page before trusting the website audiences (Meta's Events Manager shows this).
- Audiences take time to populate — a brand-new audience may show a small or "below threshold" size until enough people match. That's normal.
- If a website audience stays empty, the pixel probably isn't on that page or the path rule doesn't match the real URL.
