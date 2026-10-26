# Presentation design system

## Canvas

- Aspect ratio: 16:9
- Design target: 1600x900
- Each `.slide` fills the viewport and clips internal overflow
- Keep important content inside a 7% safe area on all sides
- Use `clamp()` for HTML type so smaller screens remain readable

## Type

- Title: 64 to 120px depending on length
- Slide headline: 48 to 76px
- Supporting line: 24 to 34px
- Labels: 16 to 20px, uppercase, letter-spaced
- SVG primary labels: 28 to 40px
- SVG secondary labels: 20 to 28px
- SVG absolute floor: 18px

Use short lines. If a headline needs more than three lines, rewrite it.

## Density

- One idea per slide
- Usually one headline plus one visual
- Keep body copy to 3 short lines or fewer
- Use 50 to 60 percent less text than a document page
- Let the presenter supply the explanation live

## Visual hierarchy

1. Headline
2. Main diagram, number, screenshot, or comparison
3. One short supporting line
4. Quiet slide number and progress

Every content slide must have a useful visual. Title and section-divider slides may be type-only.

## Layout patterns

- Hero: centered or left-anchored giant statement
- Split: claim on one side, diagram or proof on the other
- Timeline: 3 to 5 stages on one horizontal axis
- Comparison: two columns with one obvious difference
- Hub: one center idea and 3 to 5 connected parts
- Layered stack: foundation at bottom, outcomes at top
- Big proof: one number or screenshot dominates the slide

Do not default to equal card grids. Connected ideas should look connected.

## Diagram rules

- Use one flow direction per diagram
- Prefer rounded connectors and avoid crossing lines
- Put labels outside icon bodies
- Divide SVGs into top labels, middle visuals, and bottom explanations
- Enlarge the viewBox before shrinking text
- Use the payoff accent only for the one important node or change

## Motion

- Keep transitions quick and quiet
- Fade or move elements by 8 to 16px
- Reveal in reading order
- Respect reduced-motion preferences
- Never animate continuously during a talk

## Navigation

- Right arrow, down arrow, Page Down, or space: next slide
- Left arrow, up arrow, or Page Up: previous slide
- Home: first slide
- End: last slide
- Number keys may jump only when the mapping is obvious
- Update the URL hash so a slide can be reopened directly

## Accessibility

- Maintain strong foreground/background contrast
- Do not use color as the only meaning
- Give every SVG a useful `aria-label`
- Use real heading order and semantic sections
- Keep focus styles visible for buttons

## Final visual check

Inspect every slide at 1600x900 and 1280x720. Check first, middle, and last navigation; all slides for overflow; every label for collisions; and the browser for errors. Fix the source, then recheck.

