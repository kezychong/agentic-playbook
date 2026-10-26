# Themes and editable settings

Themes change the page skin, not the page meaning. The same named roles must keep the same job in every theme.

## Default: Studio

Studio is the default. It uses a dark ink masthead, a light paper reading surface, white cards, cobalt actions, and system fonts.

| Role | Studio value | Job |
|---|---|---|
| ink | `#0B0C0F` | headings and dark masthead |
| ink-2 | `#14161B` | dark footer or closing panel |
| paper | `#F5F6F9` | reading surface |
| white | `#FFFFFF` | cards and diagram panels |
| action | `#2850E8` | buttons, links, recommendation |
| action-strong | `#3A62FF` | action on dark surfaces |
| wash | `#E5EBFF` | calm blue panel |
| meaningful | `#E85D4F` | one important emphasis |
| muted | `#8A93A6` | dark-surface micro-labels and non-text graphics only |
| body | `#4A4F5A` | readable body text |
| light-line | `#E6E9EE` | light border |
| dark-line | `#1F2229` | dark border |

Studio uses these offline-safe stacks:

```css
--font-sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--font-serif:Georgia,"Times New Roman",serif;
--font-mono:ui-monospace,"SF Mono",Menlo,Monaco,Consolas,monospace;
```

Studio does not include a logo, wordmark, personal name, or company name in the member pack.

Silver or muted is reserved for dark surfaces and non-text graphics. It is not general text on light paper. Use the body or ink role for light-paper labels, footer copy, descriptions, and other readable text so contrast stays strong.

## Alternate: Warm paper

Warm paper follows the original ivory, clay, oat, olive, rust, and serif report feel.

| Role | Warm paper value | Job |
|---|---|---|
| ink | `#141413` | headings and dark text |
| ink-2 | `#25251F` | dark footer |
| paper | `#FAF9F5` | reading surface |
| white | `#FFFFFF` | cards |
| action | `#B85C3E` | links and action |
| action-strong | `#D97757` | active emphasis |
| wash | `#E3DACC` | warm panel |
| meaningful | `#D97757` | one important emphasis |
| safe | `#788C5D` | done or safe |
| risk | `#B04A3F` | blocked or high risk |
| muted | `#87867F` | micro-labels |
| body | `#3D3D3A` | readable body text |
| light-line | `#D1CFC5` | borders |

Warm paper uses the same system sans, Georgia serif, and system mono stacks unless the member chooses a different offline-safe stack.

## Member brand mapping

A member can request a custom brand after seeing the default page. Map their colors to these roles:

- `ink`: darkest readable text or masthead.
- `paper`: main page background.
- `white`: card background.
- `action`: links, buttons, and recommendation.
- `wash`: quiet emphasis surface.
- `meaningful`: one scarce highlight.
- `muted`: small labels only.
- `body`: normal reading text.
- `light-line`: light borders.
- `dark-line`: dark borders.

Keep contrast strong. Do not use a light brand color for body text. Keep one action color across buttons, diagrams, and links.

For Studio, headings stay system sans at weight 700, with key words or phrases in Georgia italic. Warm paper may use serif-led display headings. This typography distinction belongs to the theme; it does not change the page structure or meaning.

## Font choices

System fonts are the default and the offline guarantee. A member may opt into a self-hosted, embedded, or approved online font later. The page must still work when that font is unavailable.

Do not add an online font just to make a draft look complete. Never make a font download a setup requirement.

## Settings workflow

Start with Studio and project-relative settings. The agent may update `templates/theme-settings.json` for the current project, or copy its values into the page. Do not ask a member to edit JSON.

If the member asks for a custom look, change role values and preserve the layout, contrast, diagram rules, and type sizes. A theme is a real mapping, not a color-name swap.
