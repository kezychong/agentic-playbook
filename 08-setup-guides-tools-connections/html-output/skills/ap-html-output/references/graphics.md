# HTML Output graphics recipes

Graphics explain the shape of the work. They are not wallpaper. If the page names a flow, process, timeline, comparison, chart, or system, draw it with inline SVG or a responsive HTML visual.

## 1. Shared graphic rules

SVG means a small drawing written into the HTML page. Keep it inline so the page opens offline.

- Put every diagram in a white panel with a 1.5px border and 20px radius.
- Add a visible nearby title, an SVG `title`, an SVG `desc`, and a caption.
- Start the caption with “How to read it:” and explain colors, arrows, and order.
- Use mono text inside diagrams, at least 12px in the source view.
- Use dark ink for titles and readable body gray for labels.
- Use white node fills and gray borders.
- Use cobalt for the main or recommended path.
- Use a dashed rust line only for blocked, no, or unsafe paths.
- Use one shared arrow marker and one shared shadow filter.
- Keep labels at least 16px inside node edges.
- Keep at least 48px between parallel lines and unrelated nodes.
- Keep no more than eight nodes in one branching diagram.

For real evidence, use the real artifact and caption what to notice. Inspect screenshots for PII, redact it, and re-inspect before approved external sharing. Fictional demos and schematic mockups must be labeled. Inline or embedded images and lightweight motion or video are optional only when relevant and explicitly requested; an ordinary report does not need motion, and no diagram may depend on a remote asset.

Shared SVG classes keep copied recipes readable and semantically colored:

```css
.nt{font:700 18px/1.2 var(--sans);\66 ill:var(--ink)}
.ns{font:500 14px/1.3 var(--mono);\66 ill:var(--ash-700)}
.lg{font:700 13px/1.2 var(--mono);letter-spacing:.08em;text-transform:uppercase;\66 ill:var(--ash-700)}
.def{\66 ill:none;stroke:var(--ash-700);stroke-width:1.5}
.yes{\66 ill:none;stroke:var(--cobalt);stroke-width:1.5}
.no{\66 ill:none;stroke:var(--coral-deep);stroke-width:1.5;stroke-dasharray:8 6}
.value{font:700 18px/1 var(--mono);\66 ill:var(--ink)}
.label{font:500 15px/1.2 var(--mono);\66 ill:var(--ash-700)}
.axis{font:500 14px/1.2 var(--mono);\66 ill:var(--ash-700)}
```

```html
<figure class="diagram">
  <h3>Visible diagram title</h3>
  <svg viewBox="0 0 720 280" role="img" aria-labelledby="chart-title chart-desc">
    <title id="chart-title">Short description of the diagram</title>
    <desc id="chart-desc">What the reader should learn from the shapes and arrows.</desc>
    <rect width="720" height="280" fill="var(--white)"/>
  </svg>
  <figcaption>How to read it: solid cobalt means the recommended path.</figcaption>
</figure>
```

## 2. Flowchart discipline

Use one axis per diagram. Choose top to bottom or left to right.

- Never route an arrow backwards.
- Never let two lines cross.
- Split branches symmetrically from a decision.
- Rejoin both branches at one merge point.
- Use rounded elbows with a `Q` or `A` curve.
- Put yes and no labels beside, never on top of, their lines.
- Keep nodes on a grid.
- Use a diamond only for a real decision.
- Use a stepper for a straight sequence without branching.

If a diagram needs more than eight nodes, split it into two views or use a stepper. Calm geometry is more useful than showing every detail at once.

## 3. Dependency map with an emphasis node

Use boxes and arrows for a genuine branch or dependency. For a one-way sequence, use the stepper below. The `.hot` node is the one action the reader should notice.

```html
<svg viewBox="0 0 720 370" role="img" aria-labelledby="map-title map-desc">
  <title id="map-title">One source feeds two dependent steps</title>
  <desc id="map-desc">One source branches to shaping and review, then both dependencies converge on one emphasized page.</desc>
  <defs>
    <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L0 8 L8 4z" fill="var(--ash-700)"/></marker>
  </defs>
  <g class="node"><rect x="270" y="24" width="180" height="64" rx="12" fill="var(--white)" stroke="var(--line-light)" stroke-width="1.5"/><text x="360" y="53" text-anchor="middle" class="nt">Source</text><text x="360" y="74" text-anchor="middle" class="ns">raw material</text></g>
  <path d="M360 88 V118 H204 V154" class="def" marker-end="url(#flow-arrow)"/>
  <path d="M360 88 V118 H516 V154" class="def" marker-end="url(#flow-arrow)"/>
  <g class="node"><rect x="114" y="158" width="180" height="72" rx="12" fill="var(--white)" stroke="var(--line-light)" stroke-width="1.5"/><text x="204" y="189" text-anchor="middle" class="nt">Shape</text><text x="204" y="211" text-anchor="middle" class="ns">clear structure</text></g>
  <g class="node"><rect x="426" y="158" width="180" height="72" rx="12" fill="var(--white)" stroke="var(--line-light)" stroke-width="1.5"/><text x="516" y="189" text-anchor="middle" class="nt">Review</text><text x="516" y="211" text-anchor="middle" class="ns">safe choices</text></g>
  <path d="M204 230 V260 H360 V282" class="def" marker-end="url(#flow-arrow)"/>
  <path d="M516 230 V260 H360 V282" class="def" marker-end="url(#flow-arrow)"/>
  <g class="node hot"><rect x="270" y="286" width="180" height="60" rx="12" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="1.5"/><text x="360" y="312" text-anchor="middle" class="nt">Show</text><text x="360" y="333" text-anchor="middle" class="ns">one page</text></g>
</svg>
```

The source branches into two dependent steps, then both paths converge. No connector crosses a node.

## 4. Branch and merge flow

Use this only when a real choice creates two paths. Keep the spine centered.

```html
<svg viewBox="0 0 720 620" role="img" aria-labelledby="branch-title branch-desc">
  <title id="branch-title">Choose, follow a path, then merge</title>
  <desc id="branch-desc">A centered decision splits into equal left and right paths. Both paths rejoin below.</desc>
  <defs>
    <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0B0C0F" flood-opacity=".08"/></filter>
    <marker id="default-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L0 8 L8 4z" fill="var(--ash-700)"/></marker>
    <marker id="yes-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L0 8 L8 4z" fill="var(--cobalt)"/></marker>
    <marker id="no-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L0 8 L8 4z" fill="var(--coral-deep)"/></marker>
  </defs>
  <rect x="270" y="24" width="180" height="54" rx="27" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="360" y="57" text-anchor="middle" class="nt">Start</text>
  <line x1="360" y1="78" x2="360" y2="116" class="def" marker-end="url(#default-arrow)"/>
  <path d="M360 120 L438 172 L360 224 L282 172Z" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="360" y="168" text-anchor="middle" class="nt">Decision</text><text x="360" y="188" text-anchor="middle" class="ns">yes or no?</text>
  <path d="M282 172 H224 Q210 172 210 186 V272" class="yes" marker-end="url(#yes-arrow)"/>
  <text x="235" y="164" class="lg">yes</text>
  <rect x="126" y="274" width="168" height="60" rx="12" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="210" y="300" text-anchor="middle" class="nt">Safe path</text><text x="210" y="320" text-anchor="middle" class="ns">bounded test</text>
  <path d="M438 172 H496 Q510 172 510 186 V272" class="no" marker-end="url(#no-arrow)"/>
  <text x="462" y="164" class="lg">no</text>
  <rect x="426" y="274" width="168" height="60" rx="12" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="510" y="300" text-anchor="middle" class="nt">Pause path</text><text x="510" y="320" text-anchor="middle" class="ns">keep current state</text>
  <path d="M210 334 V372 Q210 386 224 386 H360" class="def"/>
  <path d="M510 334 V372 Q510 386 496 386 H360" class="def"/>
  <line x1="360" y1="386" x2="360" y2="426" class="def" marker-end="url(#default-arrow)"/>
  <rect x="270" y="430" width="180" height="60" rx="12" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="360" y="456" text-anchor="middle" class="nt">Merge</text><text x="360" y="476" text-anchor="middle" class="ns">one next action</text>
  <line x1="360" y1="490" x2="360" y2="528" class="def" marker-end="url(#default-arrow)"/>
  <rect x="270" y="532" width="180" height="54" rx="27" fill="var(--white)" stroke="var(--line-light)" filter="url(#node-shadow)"/>
  <text x="360" y="565" text-anchor="middle" class="nt">Done</text>
</svg>
```

The left and right branches have equal offsets. Both return to one centered merge. Keep the legend outside the connector paths when one is needed.

## 5. Horizontal stepper

Use a stepper for a linear sequence. Do not draw boxes and arrows for a straight pipeline.

```html
<ol class="stepper" aria-label="Linear sequence">
  <li class="done"><span>1</span><b>Gather</b><i>full input</i></li>
  <li class="done"><span>2</span><b>Shape</b><i>pick template</i></li>
  <li class="current"><span>3</span><b>Show</b><i>draw the page</i></li>
</ol>
```

```css
.stepper{list-style:none;display:flex;margin:20px 0;padding:0}
.stepper li{position:relative;flex:1;text-align:center;padding:48px 8px 0;min-width:0}
.stepper li::before{content:"";position:absolute;left:-50%;right:50%;top:17px;height:2px;background:var(--line-light)}
.stepper li:first-child::before{display:none}
.stepper li>span{position:absolute;top:0;left:50%;transform:translateX(-50%);width:36px;height:36px;display:grid;place-items:center;border:1.5px solid var(--line-light);border-radius:50%;background:var(--paper);color:var(--cobalt);font:600 14px var(--mono)}
.stepper li.current>span{background:var(--cobalt);color:var(--white);border-color:var(--cobalt)}
.stepper b,.stepper i{display:block;font-family:var(--mono);font-size:13px;color:var(--ink)}
.stepper i{font-size:12px;color:var(--ash-700);font-style:normal;margin-top:3px}
@media(max-width:560px){.stepper{display:grid;gap:14px}.stepper li{text-align:left;padding:0 0 0 52px}.stepper li::before{left:17px;right:auto;top:-14px;width:2px;height:100%}.stepper li:first-child::before{display:none}.stepper li>span{left:0;transform:none}}
```

The phone layout becomes a vertical stepper. Text remains the same size.

## 6. Bar chart with real values

Use a bar chart when the source contains measured categories. Include a zero baseline, unit, exact labels, and source/as-of note.

```html
<figure class="diagram data-chart">
  <h3>Sample workload by task</h3>
  <svg viewBox="0 0 720 350" role="img" aria-labelledby="bar-title bar-desc">
    <title id="bar-title">Sample weekly hours by repeat admin task</title>
    <desc id="bar-desc">Customer replies six hours, invoice follow-ups four hours, booking changes 2 hours.</desc>
    <line x1="90" y1="260" x2="680" y2="260" stroke="var(--ash-700)" stroke-width="1.5"/>
    <line x1="90" y1="60" x2="90" y2="260" stroke="var(--ash-700)" stroke-width="1.5"/>
    <text x="42" y="264" class="axis">0</text><text x="42" y="198" class="axis">2</text><text x="42" y="132" class="axis">4</text><text x="42" y="66" class="axis">6</text>
    <rect x="140" y="60" width="120" height="200" rx="8" fill="var(--cobalt)"/><text x="200" y="48" text-anchor="middle" class="value">6</text><text x="200" y="288" text-anchor="middle" class="label">Customer replies</text>
    <rect x="330" y="127" width="120" height="133" rx="8" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="1.5"/><text x="390" y="115" text-anchor="middle" class="value">4</text><text x="390" y="288" text-anchor="middle" class="label">Invoice follow-ups</text>
    <rect x="520" y="193" width="120" height="67" rx="8" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="1.5"/><text x="580" y="181" text-anchor="middle" class="value">2</text><text x="580" y="288" text-anchor="middle" class="label">Booking changes</text>
    <text x="90" y="326" class="axis">Hours per week · zero baseline</text>
  </svg>
  <figcaption>How to read it: each bar is measured sample workload. Source: fictional brief. As of: local page date.</figcaption>
</figure>
```

The labels must not depend on color alone. If a chart has no reliable data, replace it with “not measured” and explain what input would make it measurable.

## 7. Mobile chart repair

Do not force a 720px chart onto a 390px phone. Use a separate tall mobile version when labels need room.

```html
<svg class="chart-desktop" viewBox="0 0 720 350" aria-hidden="true">...</svg>
<svg class="chart-mobile" viewBox="0 0 340 500" role="img" aria-labelledby="mobile-title mobile-desc">
  <title id="mobile-title">Sample workload by task</title>
  <desc id="mobile-desc">The same three exact values shown as a tall chart.</desc>
  <line x1="58" y1="36" x2="58" y2="410" stroke="var(--ash-700)" stroke-width="1.5"/>
  <line x1="58" y1="410" x2="320" y2="410" stroke="var(--ash-700)" stroke-width="1.5"/>
  <rect x="58" y="78" width="252" height="42" rx="8" fill="var(--cobalt)"/>
  <text x="48" y="105" text-anchor="end" class="value">6</text><text x="58" y="150" class="label">Customer replies</text>
  <rect x="58" y="208" width="168" height="42" rx="8" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="1.5"/>
  <text x="48" y="235" text-anchor="end" class="value">4</text><text x="58" y="280" class="label">Invoice follow-ups</text>
  <rect x="58" y="338" width="84" height="42" rx="8" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="1.5"/>
  <text x="48" y="365" text-anchor="end" class="value">2</text><text x="58" y="430" class="label">Booking changes</text>
  <text x="58" y="468" class="axis">Hours per week · zero baseline</text>
</svg>
```

```css
.diagram svg.chart-desktop{display:block}
.diagram svg.chart-mobile{display:none}
@media(max-width:560px){
  .diagram svg.chart-desktop{display:none}
  .diagram svg.chart-mobile{display:block;width:100%;height:auto}
  .chart-mobile .axis,.chart-mobile .value,.chart-mobile .label{font-size:18px}
}
```

Use a labeled local scroll only when a dense diagram cannot be redrawn. Tell the reader that the panel scrolls sideways. A tall or stacked layout is preferred.

## 8. Before and after comparison

Use a comparison figure for teaching pages. Label both sides and mark it as a schematic when it is not a real screenshot.

```html
<figure class="diagram comparison">
  <h3>From wall of text to decision page</h3>
  <svg viewBox="0 0 720 320" role="img" aria-labelledby="compare-title compare-desc">
    <title id="compare-title">Wall of text compared with a decision page</title>
    <desc id="compare-desc">A plain document with lines sits beside a page with a heading, chart, and choices.</desc>
    <g transform="rotate(-2 190 160)"><rect x="70" y="40" width="240" height="240" rx="10" fill="var(--white)" stroke="var(--line-light)"/><g stroke="var(--silver)" stroke-width="4" opacity=".6" stroke-linecap="round"><line x1="92" y1="70" x2="288" y2="70"/><line x1="92" y1="94" x2="288" y2="94"/><line x1="92" y1="118" x2="270" y2="118"/><line x1="92" y1="142" x2="288" y2="142"/><line x1="92" y1="166" x2="250" y2="166"/><line x1="92" y1="190" x2="288" y2="190"/><line x1="92" y1="214" x2="278" y2="214"/><line x1="92" y1="238" x2="240" y2="238"/></g></g>
    <text x="190" y="304" text-anchor="middle" class="lg">wall of text</text>
    <g transform="rotate(1.5 530 160)"><rect x="410" y="40" width="240" height="240" rx="10" fill="var(--white)" stroke="var(--line-light)"/><rect x="432" y="66" width="130" height="14" rx="4" fill="var(--ink)"/><rect x="432" y="91" width="82" height="8" rx="4" fill="var(--cobalt)"/><rect x="432" y="120" width="24" height="44" rx="4" fill="var(--wash)"/><rect x="464" y="106" width="24" height="58" rx="4" fill="var(--cobalt)"/><rect x="496" y="132" width="24" height="32" rx="4" fill="var(--wash)"/><rect x="432" y="187" width="58" height="34" rx="6" fill="var(--paper)" stroke="var(--line-light)"/><rect x="510" y="187" width="58" height="34" rx="6" fill="var(--wash)" stroke="var(--cobalt)"/><line x1="490" y1="204" x2="510" y2="204" stroke="var(--ash-700)" stroke-width="1.5"/><rect x="432" y="238" width="170" height="8" rx="4" fill="var(--line-light)"/></g>
    <text x="530" y="304" text-anchor="middle" class="lg">decision page</text>
  </svg>
  <figcaption>How to read it: the left is a schematic wall. The right groups the answer, evidence, and choices.</figcaption>
</figure>
```

On a phone, stack the two mini-documents as two separate figures or use a tall `viewBox`. Do not shrink both to unreadable width.

## 9. Option icon sketches

Every option or template card gets a small schematic. Keep the drawing simple and label the option in HTML below it.

```html
<!-- reply drafts -->
<svg viewBox="0 0 180 110" role="img" aria-label="A message card beside a draft card"><rect x="22" y="25" width="54" height="42" rx="8" fill="var(--wash)" stroke="var(--cobalt)"/><path d="M76 46 H104" stroke="var(--ash-700)" stroke-width="2"/><rect x="104" y="17" width="54" height="58" rx="8" fill="var(--white)" stroke="var(--line-light)"/><line x1="115" y1="32" x2="148" y2="32" stroke="var(--cobalt)" stroke-width="3"/><line x1="115" y1="45" x2="143" y2="45" stroke="var(--line-light)" stroke-width="3"/><line x1="115" y1="58" x2="136" y2="58" stroke="var(--line-light)" stroke-width="3"/></svg>
<!-- payment reminders -->
<svg viewBox="0 0 180 110" role="img" aria-label="An invoice card with a reminder clock"><rect x="36" y="18" width="66" height="72" rx="8" fill="var(--white)" stroke="var(--line-light)"/><line x1="49" y1="36" x2="88" y2="36" stroke="var(--cobalt)" stroke-width="4"/><line x1="49" y1="52" x2="86" y2="52" stroke="var(--line-light)" stroke-width="4"/><circle cx="126" cy="55" r="25" fill="var(--wash)" stroke="var(--cobalt)" stroke-width="2"/><path d="M126 42 V56 L137 62" fill="none" stroke="var(--cobalt)" stroke-width="3"/></svg>
<!-- booking changes -->
<svg viewBox="0 0 180 110" role="img" aria-label="A calendar with a changed date"><rect x="37" y="22" width="72" height="66" rx="8" fill="var(--white)" stroke="var(--line-light)"/><line x1="37" y1="42" x2="109" y2="42" stroke="var(--cobalt)" stroke-width="3"/><circle cx="57" cy="61" r="5" fill="var(--wash)"/><circle cx="74" cy="61" r="5" fill="var(--cobalt)"/><circle cx="91" cy="61" r="5" fill="var(--wash)"/><path d="M124 55 H153" stroke="var(--ash-700)" stroke-width="2"/><path d="M145 47 L153 55 L145 63" fill="none" stroke="var(--ash-700)" stroke-width="2"/></svg>
```

## 10. Ring or cycle

Use a ring only for a repeated cycle. Do not use it for a one-way roadmap.

```html
<svg viewBox="0 0 260 260" role="img" aria-label="A four-part review cycle">
  <circle cx="130" cy="130" r="88" fill="none" stroke="var(--line-light)" stroke-width="14"/>
  <path d="M130 42 A88 88 0 0 1 218 130" fill="none" stroke="var(--cobalt)" stroke-width="14" stroke-linecap="round"/>
  <circle cx="130" cy="42" r="9" fill="var(--white)" stroke="var(--cobalt)" stroke-width="2"/>
  <circle cx="218" cy="130" r="9" fill="var(--white)" stroke="var(--cobalt)" stroke-width="2"/>
  <circle cx="130" cy="218" r="9" fill="var(--white)" stroke="var(--line-light)" stroke-width="2"/>
  <circle cx="42" cy="130" r="9" fill="var(--white)" stroke="var(--line-light)" stroke-width="2"/>
  <text x="130" y="126" text-anchor="middle" class="nt">Review</text><text x="130" y="146" text-anchor="middle" class="ns">then repeat</text>
</svg>
```

## 11. Clickable diagram details

For a diagram with a few steps, make each node a button-like SVG group with a `data-key`. Put the plain explanation in an adjacent detail panel. The panel must also contain a useful default explanation for readers who do not click.

Use `textContent` to replace detail text. Do not use `innerHTML` with page content or notes.

## 12. Hover-linked glossary

A glossary term may highlight its matching definition on pointer hover. The definition must remain visible at the bottom for touch devices and print.

```html
<a class="term" href="#term-sidecar" data-term="sidecar">sidecar</a>
<dl class="glossary"><dt id="term-sidecar" data-term="sidecar">Sidecar</dt><dd>A short Markdown note saved beside the page.</dd></dl>
```

```js
document.querySelectorAll('.term').forEach(term=>{
  const definition=[...document.querySelectorAll('.glossary dt[data-term]')].find(item=>item.dataset.term===term.dataset.term);
  if(!definition || definition===term) return;
  const on=()=>{term.classList.add('highlight');definition.classList.add('highlight')};
  const off=()=>{term.classList.remove('highlight');definition.classList.remove('highlight')};
  term.addEventListener('mouseenter',on);term.addEventListener('mouseleave',off);
  term.addEventListener('focus',on);term.addEventListener('blur',off);
});
```

## 13. Tabs and code samples

Use tabs for real variants such as “page view” and “copy-back view.” Each button must switch visible content. Use hand-written token spans if a code example is necessary. Do not load a code highlighter.

Keep code blocks on a dark ink panel and allow local horizontal scrolling. Code is evidence, not the main reading path. Explain what the member should notice before showing it.

## 14. Numbered walkthrough

Use numbered badges for manual actions. Each step must say what to do and where the member does it. Add a copy-as-prompt button when the step starts an agent task.

```html
<ol class="walkthrough">
  <li><span class="badge">1</span><div><b>Choose the cards</b><p>Answer only the decisions you understand.</p></div></li>
  <li><span class="badge">2</span><div><b>Copy the verdicts</b><p>Inspect the full block before copying.</p></div></li>
  <li><span class="badge">3</span><div><b>Paste into your agent</b><p>Ask it to continue from those answers.</p></div></li>
</ol>
```

## 15. Responsive and print checks

For every page, test widths near 1440, 768, 390, and 320 CSS pixels.

- At 840px, reduce multi-column grids.
- At 560px, stack cards and use tall diagrams.
- Keep an SVG `viewBox` and labels matched to each layout.
- Keep no diagram text below 12px after rendering.
- Keep buttons and labels at least 44px tall.
- Use `min-width:0` on all grid children.
- Never let a sticky panel hide a control.
- Add visible keyboard focus.
- Remove motion under `prefers-reduced-motion`.
- Hide copy buttons in print, but keep the decision text and diagrams.

When a wide diagram truly needs local scrolling, use a labeled panel such as “Scroll sideways inside this diagram.” This is an intentional exception, not the default mobile strategy.

## 16. Artifact mapping

| Page type | First useful picture |
|---|---|
| Status | measured bar chart and progress bar |
| Plan or roadmap | responsive stepper and milestone timeline |
| Review | risk map or branch-and-merge choice |
| Research or explainer | before-and-after figure and concept diagrams |
| Options | one schematic sketch per card |
| Teaching | before-and-after figure and numbered walkthrough |

If there is no honest data, draw the structure and label it as a schematic. Never turn a decorative shape into a fake result.
