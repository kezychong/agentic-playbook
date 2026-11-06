# Reference images, embedded media, and CJK text

## Translate references without copying identity

A reference image may guide visual attributes, not authorship or affiliation.

1. Describe the high-level traits: palette, contrast, type category, spacing, alignment, image crop, texture, border treatment, and visual rhythm.
2. Choose a small set of traits that serve the deck's purpose.
3. Rebuild them with original layout, typography, diagrams, and permitted assets.
4. Remove logos, wordmarks, signatures, mascots, distinctive characters, and other identity markers unless the user owns or is authorized to use them.
5. Compare the result with the reference. If it looks like a replica or could imply affiliation, change the composition and asset treatment.

Do not claim that a deck is “in the style of” a named person or brand. Describe the resulting attributes instead, such as “high-contrast editorial layout with narrow captions.”

## Image rights and evidence

Use user-supplied, licensed, public-domain, or newly created assets within their permitted scope. Do not infer permission from public availability. Keep attribution when the license or user requires it.

For screenshots and evidence images:

- caption what the audience should notice;
- preserve relevant context and do not crop away contradictory evidence;
- redact personal data, account identifiers, and secrets before embedding;
- inspect the redacted copy again;
- label fictional, schematic, or generated images.

## Embedding images

For a self-contained deck, encode approved raster images as `data:` URLs and keep SVG inline. Use a supported image type such as PNG, JPEG, WebP, or SVG.

- Set explicit width and height or an aspect ratio to prevent layout jumps.
- Use `object-fit` deliberately; do not stretch images.
- Add useful `alt` text when the image carries meaning. Use empty alt text only for decoration.
- Keep evidence captions as real HTML text.
- Resize oversized images before embedding, but do not make text inside screenshots unreadable.
- If the deck becomes impractically large, ask before switching to project-relative assets.
- Never use a remote URL in an offline deck.

After saving the HTML, disconnect from the network or block requests and confirm every image still loads.

## CJK guidance

CJK covers Chinese, Japanese, and Korean text. Set the document language and use a font stack that has glyph coverage for the actual language.

Example system stacks:

```css
:lang(zh-CN){font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif}
:lang(zh-TW){font-family:"PingFang TC","Microsoft JhengHei","Noto Sans CJK TC",sans-serif}
:lang(ja){font-family:"Hiragino Sans","Yu Gothic","Noto Sans CJK JP",sans-serif}
:lang(ko){font-family:"Apple SD Gothic Neo","Malgun Gothic","Noto Sans CJK KR",sans-serif}
```

- Set `<html lang="...">` and `lang` on passages that switch language.
- Do not apply Latin uppercase transforms or wide letter spacing to CJK text.
- Use comfortable line height, usually 1.35 to 1.6, and allow more vertical room than an English-only layout.
- Prefer natural phrase breaks. Avoid single punctuation marks or isolated characters at line edges when practical.
- Use `word-break: keep-all` selectively for Korean and short CJK headings; test long strings rather than applying it blindly.
- Keep important CJK text as HTML or SVG text, not rasterized inside a generated image.
- Confirm punctuation, numerals, bold weights, fallback glyphs, and mixed Latin/CJK lines in the rendered browser.
- Review at both target viewport sizes with a fluent reader when wording quality matters.
