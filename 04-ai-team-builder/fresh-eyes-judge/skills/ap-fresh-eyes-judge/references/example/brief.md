---
stage: draft
---
# Practice brief
Create a landing page draft for a fictional bakery.
C1: Include the exact heading "Fresh bread, ready daily".
C2: Include a button label reading exactly "Reserve a loaf".
No design, publication, or live button behavior is required.
Run these checks from the folder containing this brief and the draft:
`grep -nFx '# Fresh bread, ready daily' landing-page.md`
`grep -nFx '[Reserve a loaf]' landing-page.md`
Both checks must exit 0 before PASS.
