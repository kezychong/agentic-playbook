# Voice Recognition

**Agentic Playbook — by Kezy**

This is one package, retaining the supplied grouping and its supporting files. It is a local source draft, not an installed or runtime-tested system.

## Included skills
- [Voice Recognition](skills/ap-voice-recognition/README.md): Match a speaker's voice sample against saved voice profiles, with every low-confidence match held for human confirmation.

## Setup
1. Read each included skill README and its prerequisites.
2. Keep every skill folder and all its support files together.
3. Review the documented host setup before copying anything into an installation.
4. Use fictional inputs first. Loading a skill does not approve installation, external actions or spending.

[Host setup guide](../../08-setup-guides-tools-connections/manual-setup.md)


## Relationship to other packages
This package complements [ap-meeting-intelligence](../meeting-intelligence/skills/ap-meeting-intelligence/README.md): meeting-intelligence produces minutes from generic speaker labels, and this skill can optionally resolve one of those labels to a saved identity if the human has approved profiles to match against. It is not a hard dependency of that package; meeting-intelligence works fully without it.

## Limits and reuse
Source scripts, account connections, installations and host behaviour have not been exercised in this build. Some optional components need additional software, verified compatibility or paid access. Preserve required legal notices. The collection is maintained by Kezy; no new blanket redistribution licence is implied.

<!-- Agentic Playbook — by Kezy -->
