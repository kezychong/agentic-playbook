# Design Templates — Full Reference

Every template starts from one `BRAND_PRIMARY` hex, and the same five derived colors get built from it every time. Use your own brand hex to override the primary color, the derivation rules below stay identical regardless of which color you start from.

## Color Derivation Rules

From `BRAND_PRIMARY`, derive:

- `BRAND_LIGHT` — `BRAND_PRIMARY` lightened by roughly 20% (mix with white)
- `BRAND_DARK` — `BRAND_PRIMARY` darkened by roughly 30% (mix with black)
- `LIGHT_BG` — a tinted off-white using a whisper of `BRAND_PRIMARY`, never pure `#FFFFFF`
- `LIGHT_BORDER` — a shade slightly darker than `LIGHT_BG`, same tint direction
- `DARK_BG` — near-black with a warm or cool tint pulled from `BRAND_PRIMARY` (warm colors get a warm-tinted dark, cool colors get a cool-tinted dark)

Gradient formula, used on high-impact slides (slide 3 and the final CTA):

```css
linear-gradient(165deg, BRAND_DARK 0%, BRAND_PRIMARY 50%, BRAND_LIGHT 100%)
```

The angle and stop positions stay fixed across every template. Only the three colors change.

---

## 1. Editorial

- **Vibe:** premium, magazine feel
- **Fonts:** Playfair Display (heading) + DM Sans (body)
- **BRAND_PRIMARY:** `#C4553B`
- **Derived:** `BRAND_LIGHT` a warm terracotta-blush, `BRAND_DARK` a deep rust-brown, `LIGHT_BG` a warm cream, `DARK_BG` a near-black with a brown tint
- **Use when:** thought-leadership, personal brands, founder stories
- **Example topics:** "Why I stopped hiring for experience", "The 3 beliefs I had to unlearn to scale", "A day in the life of a solo founder"

## 2. Modern

- **Vibe:** clean SaaS
- **Fonts:** Plus Jakarta Sans (heading and body)
- **BRAND_PRIMARY:** `#4F46E5`
- **Derived:** `BRAND_LIGHT` a soft periwinkle, `BRAND_DARK` a deep indigo, `LIGHT_BG` a cool near-white, `DARK_BG` a near-black with a blue tint
- **Use when:** tech, startups, productivity tools
- **Example topics:** "5 features that saved us 10 hours a week", "How we cut onboarding time in half", "The stack we run our whole company on"

## 3. Warm

- **Vibe:** approachable
- **Fonts:** Lora (heading) + Nunito Sans (body)
- **BRAND_PRIMARY:** `#B45309`
- **Derived:** `BRAND_LIGHT` a soft honey, `BRAND_DARK` a deep amber-brown, `LIGHT_BG` a warm sand, `DARK_BG` a near-black with an amber tint
- **Use when:** coaches, community builders, lifestyle brands
- **Example topics:** "3 habits that changed my mornings", "What I tell every new client in week one", "The community ritual that keeps people showing up"

## 4. Technical

- **Vibe:** sharp, precise
- **Fonts:** Space Grotesk (heading and body)
- **BRAND_PRIMARY:** `#0D9488`
- **Derived:** `BRAND_LIGHT` a soft teal, `BRAND_DARK` a deep pine, `LIGHT_BG` a cool pale mint, `DARK_BG` a near-black with a teal tint
- **Use when:** dev tools, data products, AI topics
- **Example topics:** "How we cut inference cost by 40%", "The one prompt pattern that fixed our agent", "A breakdown of our RAG pipeline"

## 5. Bold

- **Vibe:** loud, expressive
- **Fonts:** Fraunces (heading) + Outfit (body)
- **BRAND_PRIMARY:** `#E11D48`
- **Derived:** `BRAND_LIGHT` a bright coral-pink, `BRAND_DARK` a deep crimson, `LIGHT_BG` a warm blush white, `DARK_BG` a near-black with a red tint
- **Use when:** hot takes, contrarian content, opinion pieces
- **Example topics:** "Unpopular opinion: most productivity advice is noise", "Why I fired my biggest client", "The advice everyone gives that is actually wrong"

## 6. Classic

- **Vibe:** trustworthy
- **Fonts:** Libre Baskerville (heading) + Work Sans (body)
- **BRAND_PRIMARY:** `#1E3A5F`
- **Derived:** `BRAND_LIGHT` a muted steel blue, `BRAND_DARK` a deep navy, `LIGHT_BG` a cool paper white, `DARK_BG` a near-black with a navy tint
- **Use when:** finance, legal, consulting
- **Example topics:** "3 numbers every business owner should check monthly", "What most contracts get wrong", "How to read a P&L in 5 minutes"

## 7. Rounded

- **Vibe:** friendly
- **Fonts:** Bricolage Grotesque (heading and body)
- **BRAND_PRIMARY:** `#059669`
- **Derived:** `BRAND_LIGHT` a soft mint green, `BRAND_DARK` a deep forest green, `LIGHT_BG` a pale sage, `DARK_BG` a near-black with a green tint
- **Use when:** health, education, family brands
- **Example topics:** "5 snacks my kids actually eat", "What I wish I knew before my first marathon", "A simple bedtime routine that worked for us"

---

See `assets/template-gallery.md` for a visual side-by-side contact sheet of all 7 templates.

*Part of the Agentic Playbook build.*
