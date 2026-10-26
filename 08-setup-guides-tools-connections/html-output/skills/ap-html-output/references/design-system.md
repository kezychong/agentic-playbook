# HTML Output design system

This is the component library for calm, readable decision reports. Use the named roles from the active theme. Do not invent a second palette inside one page.

## 1. Page tokens

Studio is the default offline theme. Its roles are:

```css
:root{
  --ink:#0B0C0F;
  --ink-2:#14161B;
  --paper:#F5F6F9;
  --white:#FFFFFF;
  --cobalt:#2850E8;
  --cobalt-bright:#3A62FF;
  --wash:#E5EBFF;
  --coral:#E85D4F;
  --coral-deep:#D14A3D;
  --silver:#8A93A6;
  --ash-700:#4A4F5A;
  --body-dark:#C8CDD8;
  --line-light:#E6E9EE;
  --line:#1F2229;
  --serif:Georgia,"Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Monaco,Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ash-700);font:18px/1.6 var(--sans)}
.wrap{width:min(1120px,100%);margin:auto;padding:0 32px}
```

Use the named roles rather than hard-coding a new color. Warm paper maps the same roles to ivory, ink, clay, olive, rust, oat, and gray values. Read `references/themes.md` before changing them.

### Type roles

- Studio headings: system sans at weight 700. Put only the key word or phrase in Georgia italic.
- Warm paper headings may use a serif-led display treatment while keeping the same named roles and sizes.
- Serif: Georgia italic emphasis and large measured values; use it for display headings in Warm paper.
- Sans: Studio headings, body copy, button labels, and card explanations.
- Mono: eyebrows, section numbers, chips, units, filenames, and status labels.

Use 18px body text. Keep card copy at least 16px. Keep mono labels at least 12.5px. Use readable line height near 1.6. Keep a prose measure near 65 to 75 characters.

### Surface roles

- `--ink`: masthead and dark closing panels.
- `--paper`: page reading surface.
- `--white`: cards and diagram panels.
- `--wash`: calm emphasis panels and safe prompt blocks.
- `--line-light`: borders on light surfaces.
- `--line`: borders on dark surfaces.

Cards use white, a 1.5px border, and a 20px radius in the Studio report skin. Pills use a full radius. Keep shadows rare and soft.

## 2. Meaning colors

Use color to explain meaning, never as decoration:

| Meaning | Studio role | Use |
|---|---|---|
| Confirmed, done, safe | cobalt or olive role | completed step, safe choice |
| Proposed, active, recommended | cobalt | action, recommendation, current step |
| Warning or one important moment | coral | one meaningful emphasis only |
| Blocked or high risk | rust role | stopped path, unsafe or high-risk item |
| Neutral or unanswered | silver and line | pending state, no selection |

Coral should appear once for a meaningful point. A teaching page may use the coral dot in its wordmark. Do not use coral for every button or label.

On light paper, use `--ash-700`, the body role, or `--ink` for all text, including footers and small labels. Silver is reserved for dark surfaces or non-text graphics, not general small labels on light paper. Preserve this contrast rule when mapping a custom brand.

## 3. Masthead

The masthead answers “What is this?” before the reader scrolls.

```html
<header class="masthead">
  <div class="wrap">
    <p class="eyebrow">PROJECT · DATE · CONTEXT</p>
    <h1>What should we <em>choose</em>?</h1>
    <p class="lead">One plain sentence explaining the page.</p>
    <div class="chips" aria-label="Page details">
      <span class="chip">owner: project role</span>
      <span class="chip">version: 2.0.0</span>
      <span class="chip">offline page</span>
    </div>
  </div>
</header>
```

```css
.masthead{background:var(--ink);color:var(--body-dark);padding:38px 0 58px}
.masthead h1{color:var(--white);font:700 clamp(40px,6vw,72px)/1.08 var(--sans);letter-spacing:-.03em;margin:18px 0}
.masthead h1 em{color:var(--cobalt-bright);font-family:var(--serif);font-style:italic;font-weight:400}
.eyebrow,.idx,.mini{font:500 12.5px/1.5 var(--mono);letter-spacing:.16em;text-transform:uppercase}
.eyebrow{color:var(--wash)}
.eyebrow::before{content:"";display:inline-block;width:26px;height:2px;margin:0 10px 4px 0;background:var(--cobalt)}
.lead{max-width:760px;font-size:21px;margin:0}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
.chip{border:1.5px solid var(--line);border-radius:999px;padding:6px 12px;font:12.5px var(--mono);color:var(--body-dark)}
```

Use the key word in an italic serif style. Do not turn the masthead into a sales banner.

## 4. Summary strip

The summary strip gives the answer in three or four facts.

```html
<section class="summary-grid" aria-label="Summary">
  <article class="stat"><strong>2 of 5</strong><span>steps measured done</span></article>
  <article class="stat"><strong>12</strong><span>sample hours per week</span></article>
  <article class="stat"><strong>1</strong><span>proposed first test</span></article>
</section>
```

```css
.summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:42px 0}
.stat{min-width:0;background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:22px}
.stat strong{display:block;color:var(--ink);font:500 clamp(30px,4vw,44px)/1 var(--serif)}
.stat span{display:block;margin-top:9px;font-size:15px}
```

Never display a number without its unit or denominator. If the source does not measure it, write “not measured.”

## 5. Where we are

Project work starts with progress and the next action.

```html
<section class="where" aria-labelledby="where-title">
  <div class="where-head"><h2 id="where-title">Where we are</h2><strong>2 of 5 steps · 40%</strong></div>
  <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="5" aria-valuenow="2" aria-label="Fictional progress: 2 of 5 steps"><i style="width:40%"></i></div>
  <p>Two sample steps are done. Three steps are next.</p>
</section>
```

```css
.where{background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:26px;margin:42px 0}
.where-head{display:flex;justify-content:space-between;gap:20px;align-items:baseline}
.where h2{margin:0;color:var(--ink);font:700 30px/1.15 var(--sans)}
.where-head strong{font:600 13px var(--mono);color:var(--cobalt)}
.progress{height:12px;margin:18px 0 10px;background:var(--line-light);border-radius:999px;overflow:hidden}
.progress i{display:block;height:100%;background:var(--cobalt);border-radius:inherit}
```

The number must show what it counts. A project without a measured denominator says “not measured” instead of showing a fake bar.

## 6. Milestone timeline

Use one row for every meaningful phase. Mark each row done, in progress, blocked, or next.

```html
<ol class="timeline">
  <li class="done"><span class="rail-dot" aria-hidden="true">1</span><div><b>List repeated questions</b><p>Sample material is ready.</p><span class="pill done">done</span></div></li>
  <li class="next"><span class="rail-dot" aria-hidden="true">2</span><div><b>Approve the test</b><p>The member chooses a safe scope.</p><span class="pill next">next</span></div></li>
</ol>
```

```css
.timeline{list-style:none;margin:20px 0;padding:0;display:grid;gap:16px}
.timeline li{display:grid;grid-template-columns:38px minmax(0,1fr);gap:14px;min-width:0}
.rail-dot{width:34px;height:34px;display:grid;place-items:center;border:1.5px solid var(--line-light);border-radius:50%;font:600 13px var(--mono);color:var(--cobalt);background:var(--white)}
.timeline li.done .rail-dot{color:var(--white);background:var(--cobalt);border-color:var(--cobalt)}
.timeline b{color:var(--ink);font:600 16px var(--sans)}
.timeline p{margin:3px 0 6px;font-size:16px}
.pill{display:inline-block;border-radius:999px;padding:3px 9px;font:700 12.5px var(--mono)}
.pill.done{color:var(--cobalt);background:var(--wash)}
.pill.next{color:var(--ash-700);background:var(--paper);border:1.5px solid var(--line-light)}
```

## Component recipes: carryover, risks, and review comments

Use these panels when a report carries work forward, explains a blockage, or records a review note. Keep the examples generic and name the safe next action.

```html
<aside class="carryover-panel" aria-labelledby="carryover-title">
  <span class="mini">CARRYOVER / BLOCKED</span>
  <h3 id="carryover-title">Keep the approved parts</h3>
  <p>The sample brief is clear enough to carry forward, but one input still blocks the next test.</p>
  <div class="carryover-rows">
    <div class="carryover-row"><b>Carry over</b><span>Keep the measured task list and the chosen review rule.</span></div>
    <div class="carryover-row blocked"><b>Blocked</b><span>Supply the missing time baseline before comparing results.</span></div>
  </div>
</aside>

<table class="risk-table">
  <caption>Risks in the sample plan</caption>
  <thead><tr><th scope="col">Risk</th><th scope="col">What it means</th><th scope="col">Safe response</th></tr></thead>
  <tbody>
    <tr><th scope="row"><span class="risk-label low">Low</span></th><td data-label="What it means">The sample labels are understood.</td><td data-label="Safe response">Keep the label and continue.</td></tr>
    <tr><th scope="row"><span class="risk-label medium">Medium</span></th><td data-label="What it means">The starting time is not measured.</td><td data-label="Safe response">Record a baseline before judging change.</td></tr>
    <tr><th scope="row"><span class="risk-label high">High</span></th><td data-label="What it means">A proposed action could send without review.</td><td data-label="Safe response">Pause and keep a person in the loop.</td></tr>
  </tbody>
</table>

<aside class="review-comment" aria-label="Review comment">
  <span class="mini">REVIEW COMMENT</span>
  <p>Keep the recommendation, but show the missing baseline beside the decision.</p>
  <cite>Sample reviewer note</cite>
</aside>
```

```css
.carryover-panel,.review-comment{min-width:0;background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:22px;margin:20px 0}
.carryover-panel{border-left:5px solid var(--cobalt)}
.carryover-panel .mini,.review-comment .mini{display:block;color:var(--cobalt);font:700 12.5px/1.4 var(--mono);letter-spacing:.08em}
.carryover-panel h3{margin:9px 0 7px;color:var(--ink);font:700 22px/1.2 var(--sans)}
.carryover-panel p,.carryover-row span,.risk-table td,.review-comment p{font-size:16px}
.carryover-panel p{margin:0 0 16px}
.carryover-rows{display:grid;gap:10px}
.carryover-row{display:grid;grid-template-columns:minmax(105px,150px) minmax(0,1fr);gap:14px;padding:12px 14px;border:1.5px solid var(--line-light);border-radius:12px;background:var(--paper)}
.carryover-row b{color:var(--cobalt);font:700 13px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em}
.carryover-row.blocked{border-left:4px solid var(--coral-deep)}
.carryover-row.blocked b{color:var(--coral-deep)}
.risk-table{width:100%;border-collapse:collapse;background:var(--white);border:1.5px solid var(--line-light);border-radius:16px;overflow:hidden;margin:24px 0}
.risk-table caption{text-align:left;color:var(--ink);font:700 20px/1.2 var(--sans);padding:18px 18px 12px}
.risk-table th,.risk-table td{padding:14px 16px;border-top:1.5px solid var(--line-light);text-align:left;vertical-align:top}
.risk-table thead th{color:var(--ink);font:700 12.5px/1.4 var(--mono);letter-spacing:.08em;text-transform:uppercase}
.risk-table tbody th{width:130px}
.risk-table td{color:var(--ash-700)}
.risk-label{display:inline-block;min-width:64px;padding:4px 8px;border:1.5px solid currentColor;border-radius:999px;text-align:center;font:700 12.5px/1.2 var(--mono);text-transform:uppercase}
.risk-label.low{color:var(--ash-700);background:var(--paper)}
.risk-label.medium{color:var(--cobalt);background:var(--wash)}
.risk-label.high{color:var(--coral-deep);background:var(--white)}
.review-comment{border-left:5px solid var(--cobalt);background:var(--wash)}
.review-comment p{margin:10px 0 8px;color:var(--ink)}
.review-comment cite{color:var(--ash-700);font-size:14px;font-style:normal}
@media(max-width:560px){
  .carryover-row{grid-template-columns:1fr;gap:5px}
  .risk-table,.risk-table thead,.risk-table tbody,.risk-table tr,.risk-table th,.risk-table td{display:block}
  .risk-table{border:0;background:transparent;overflow:visible}
  .risk-table caption{padding:0 0 10px}
  .risk-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .risk-table tr{background:var(--white);border:1.5px solid var(--line-light);border-radius:16px;margin:12px 0;padding:4px 0}
  .risk-table tbody th,.risk-table td{width:auto;padding:10px 14px;border-top:0}
  .risk-table td{display:grid;grid-template-columns:112px minmax(0,1fr);gap:10px}
  .risk-table td::before{content:attr(data-label);color:var(--ink);font:700 12.5px/1.4 var(--mono);text-transform:uppercase;letter-spacing:.06em}
}
```

## 7. Section anatomy

Number every major section. Open with the problem it solves, then show its picture, then explain the picture.

```html
<section class="section" id="options">
  <div class="wrap">
    <span class="idx">02 · OPTIONS</span>
    <h2>See the three paths</h2>
    <p class="section-lead">The workload has three different shapes. Each path trades effort for a different kind of relief.</p>
    <figure class="diagram">...</figure>
  </div>
</section>
```

Use generous vertical separation. Alternate paper and white section surfaces only when it improves orientation. Keep the reading measure narrower than the outer container.

## 8. Diagram panels

All diagrams sit in a white panel with a title, accessible description, and caption.

```css
.diagram{margin:26px 0;background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:20px;min-width:0}
.diagram svg{display:block;width:100%;height:auto}
.diagram svg.chart-mobile{display:none}
.diagram figcaption{margin-top:14px;color:var(--ash-700);font-size:14px}
```

The graphics reference contains flow, stepper, chart, comparison, ring, glossary, tabs, and walkthrough recipes. Use a small data chart for actual values, not abstract decoration.

## 9. Option and comparison cards

An options page shows three to six genuinely different paths. Every card contains a schematic picture, title, plain description, one tradeoff, and recommendation state.

```html
<div class="card-grid">
  <article class="card option-card">
    <div class="thumb" aria-hidden="true"><svg viewBox="0 0 180 110">...</svg></div>
    <h3>Reply drafts</h3>
    <p>Drafts a reply for a person to check.</p>
    <p class="tradeoff"><b>Tradeoff:</b> checking stays manual.</p>
  </article>
</div>
```

```css
.card-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.card{min-width:0;background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:22px}
.card h3{color:var(--ink);font:600 21px/1.2 var(--sans);margin:16px 0 8px}
.card p{font-size:16px;margin:0 0 12px}
.thumb{min-height:118px;display:grid;place-items:center;border-radius:14px;background:var(--paper);padding:12px}
.thumb svg{width:min(180px,100%);height:auto}
.tradeoff{color:var(--ash-700)}
```

Do not preselect an option unless the member explicitly supplied the choice. A recommendation may be visible without being the member’s answer.

## 10. Review cards

Decision cards must make the decision possible without opening another document.

```html
<article class="decision-card">
  <div class="decision-head"><span class="mini">D1</span><span class="pill next">Unanswered</span></div>
  <h3>Try reply drafts first?</h3>
  <p><b>Proposal:</b> Show the complete proposed test here.</p>
  <dl class="consequences">
    <div><dt>Confirm means</dt><dd>State the exact bounded action.</dd></div>
    <div><dt>Veto means</dt><dd>State what stays paused or manual.</dd></div>
    <div><dt>Edit means</dt><dd>State that the note supplies a replacement scope.</dd></div>
  </dl>
  <fieldset class="choice-set"><legend>Your answer</legend>...</fieldset>
  <label class="note-label">Optional note<textarea></textarea></label>
</article>
```

```css
.decision-card{min-width:0;background:var(--white);border:1.5px solid var(--line-light);border-radius:20px;padding:24px;margin:20px 0}
.decision-head{display:flex;justify-content:space-between;gap:12px;align-items:center}
.consequences{display:grid;gap:12px;margin:20px 0}
.consequences div{border-left:3px solid var(--cobalt);padding-left:14px}
.consequences dt{font:700 12.5px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--cobalt)}
.consequences dd{margin:4px 0 0;font-size:16px}
.choice-set{border:0;padding:0;margin:20px 0}
.choice-set legend{font:700 13px var(--mono);color:var(--ink);margin-bottom:10px}
.choice-set label{display:inline-flex;align-items:center;gap:8px;min-height:44px;margin:0 14px 6px 0;font-size:16px;cursor:pointer}
.choice-set input{width:20px;height:20px;accent-color:var(--cobalt)}
.note-label{display:grid;gap:7px;font-size:16px}
.note-label textarea{min-height:92px;width:100%;resize:vertical;padding:12px;border:1.5px solid var(--line-light);border-radius:10px;background:var(--paper);font:16px/1.5 var(--sans);color:var(--ink)}
```

Controls must be at least 44px high. Add a visible focus ring to buttons, links, inputs, and textareas.

## 11. Details, tabs, and contents

Use native details for full evidence. Use tabs only when the reader compares true variants.

```css
details.fold{background:var(--white);border:1.5px solid var(--line-light);border-radius:14px;padding:0 18px;margin:14px 0}
details.fold summary{cursor:pointer;padding:16px 0;color:var(--ink);font:600 18px var(--serif)}
.toc{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 34px}
.toc a{color:var(--cobalt);border:1.5px solid var(--line-light);border-radius:999px;padding:7px 13px;font:12.5px var(--mono);text-decoration:none}
```

The active tab needs an obvious state. A tab must switch actual content, not just change its label.

## 12. Copy controls

Use a clear primary button for the one important copy action. Put the full readonly result in a visible textarea so the member can inspect it.

```css
button,.button{min-height:44px;border:1.5px solid var(--cobalt);border-radius:10px;padding:10px 16px;background:var(--cobalt);color:var(--white);font:600 16px var(--sans);cursor:pointer}
button.secondary{background:var(--white);color:var(--cobalt)}
textarea.output{width:100%;min-height:180px;padding:14px;border:1.5px solid var(--line-light);border-radius:12px;background:var(--paper);color:var(--ink);font:14px/1.55 var(--mono);resize:vertical}
```

The verdict reference defines the honest clipboard fallback. A success label appears only after the write resolves.

## 13. Glossary

Glossary terms may be linked from prose with a dashed underline. Keep the bottom glossary complete even when hover is unavailable.

```css
.term{border-bottom:1.5px dashed var(--cobalt);cursor:help}
.term.highlight,.glossary dt.highlight{background:var(--wash);color:var(--ink)}
.glossary{display:grid;grid-template-columns:minmax(100px,180px) minmax(0,1fr);gap:8px 20px}
.glossary dt{color:var(--ink);font:700 13px var(--mono)}
.glossary dd{margin:0;font-size:16px}
```

Hover highlighting is optional. The plain definition is not optional.

## 14. Footer and print

The footer records the page version, local date, generic source, and real next action.

```css
footer{border-top:1.5px solid var(--line-light);margin-top:70px;padding:28px 0 80px;color:var(--ash-700);font:13px/1.6 var(--mono)}
@media print{
  body{background:white;color:#222;font-size:12pt}
  .masthead{background:white;color:#222;padding-bottom:20px}
  .masthead h1{color:#111}
  button,.button,.toc{display:none}
  .card-grid{grid-template-columns:1fr 1fr}
  .diagram{break-inside:avoid}
}
```

## 15. Responsive rules

```css
@media(max-width:840px){
  .summary-grid,.card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:560px){
  .wrap{padding:0 18px}
  .summary-grid,.card-grid{grid-template-columns:1fr}
  .masthead{padding:28px 0 44px}
  .masthead h1{font-size:clamp(38px,12vw,56px)}
  .where-head{display:block}
  .where-head strong{display:block;margin-top:10px}
}
```

Every grid child gets `min-width:0`. Stack cards on phones. Keep labels readable. Never let a sticky panel cover a decision control. Respect `prefers-reduced-motion: reduce` by removing smooth scrolling and transitions.
