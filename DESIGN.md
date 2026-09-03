---
name: SOFT_CARD (Rounded Card)
colors:
  surface: '#eef0f7'
  surface-card: '#ffffff'
  surface-secondary: '#f1f2f8'
  label: '#2b2d42'
  secondary-label: '#7a7f9a'
  tertiary-label: '#a5aac4'
  quaternary-label: '#c3c7d9'
  separator: '#e6e8f2'
  outline: '#c9cddd'
  blue: '#3b82f6'
  blue-hover: '#5c9cf8'
  blue-pressed: '#2f6fe0'
  blue-container: '#e3efff'
  blue-container-hover: '#d6e7fd'
  on-blue-container: '#1d5fd0'
  rose: '#f4506c'
  rose-hover: '#ff647e'
  rose-container: '#ffe7eb'
  rose-container-hover: '#ffd9e0'
  on-rose-container: '#b32447'
  mint: '#10b981'
  amber: '#ff9f43'
  neutral: '#8b90a8'
  chip-neutral: '#eceef5'
  chip-neutral-hover: '#e1e4ee'
typography:
  large-title:
    fontFamily: SF Pro Display
    fontSize: 28px
    fontWeight: 'bold'
    lineHeight: '1.2'
  title-1:
    fontFamily: SF Pro Display
    fontSize: 22px
    fontWeight: 'bold'
    lineHeight: '1.3'
  title-2:
    fontFamily: SF Pro Display
    fontSize: 17px
    fontWeight: 'bold'
    lineHeight: '1.3'
  title-3:
    fontFamily: SF Pro Display
    fontSize: 15px
    fontWeight: 'bold'
    lineHeight: '1.3'
  headline:
    fontFamily: SF Pro Text
    fontSize: 15px
    fontWeight: 'bold'
    lineHeight: '1.4'
  body:
    fontFamily: SF Pro Text
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  body-lg:
    fontFamily: SF Pro Text
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  caption:
    fontFamily: SF Pro Text
    fontSize: 11px
    fontWeight: '400'
    lineHeight: '1.3'
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  gutter: 24px
  margin: 28px
rounded:
  sm: 12px
  DEFAULT: 16px
  lg: 20px
  pill: 999px
components:
  button-primary:
    backgroundColor: '{colors.Blue}'
    textColor: '#ffffff'
    rounded: pill
    height: 36px
  button-primary-hover:
    backgroundColor: '{colors.blue-hover}'
  button-secondary:
    backgroundColor: '{colors.blue-container}'
    textColor: '{colors.Blue}'
    rounded: pill
  button-destructive:
    backgroundColor: '{colors.rose}'
    textColor: '#ffffff'
    rounded: pill
  button-destructive-soft:
    backgroundColor: '{colors.rose-container}'
    textColor: '{colors.rose}'
    rounded: pill
  button-neutral:
    backgroundColor: '{colors.chip-neutral}'
    textColor: '{colors.label}'
    rounded: pill
  input:
    backgroundColor: '{colors.surface-secondary}'
    textColor: '{colors.label}'
    rounded: 12px
    borderWidth: 1px
    borderColor: '{colors.separator}'
  input-focus:
    borderColor: '{colors.Blue}'
  card:
    backgroundColor: '{colors.surface-card}'
    rounded: 16px
    borderWidth: 1px
    borderColor: '{colors.separator}'
  progress-bar:
    backgroundColor: '{colors.separator}'
    fillColor: '{colors.Blue}'
    rounded: pill
    height: 8px
---

## Brand & Style

The design system is **SOFT_CARD** — a young, friendly "rounded card"
aesthetic. Pill buttons, pastel chips, white cards floating on a
lavender-mist canvas, and generous breathing room everywhere. It feels
like a modern consumer app: colorful, soft, and approachable.

This style prioritizes **roundness and color**. Actions are colorful
filled pills; destructive actions are soft rose chips, not alarm-red
buttons; surfaces are ultra-rounded tiles with hairline borders.

## Colors

The palette is anchored by **Mist** (#eef0f7) — a lavender-tinted light
gray that reads as friendlier than a neutral gray. **Card** (#ffffff)
surfaces float on it with a 1px hairline border (#e6e8f2) so tiles stay
distinct even when adjacent.

**Ink** (#2b2d42) — a deep indigo-tinged dark — carries primary text,
softer than pure black. **Slate** (#7a7f9a) handles secondary text.

**Blue** (#3b82f6) is the primary accent: bright, calm, and confident.
It fills primary buttons, progress tracks, and checkbox fills.
**Rose** (#f4506c) is the destructive accent — softer than alarm-red,
used filled for hard destructive actions and as a pale chip
(#ffe7eb + rose text) for gentle ones like "全部停止".
**Mint** (#10b981) marks success; **Amber** (#ff9f43) marks parsing.

Pastel containers round out the family: **Blue Container** (#e3efff)
for secondary chips, **Chip Neutral** (#eceef5) for tertiary buttons.

## Typography

**SF Pro Display** for titles and **SF Pro Text** for body, falling back
to **Segoe UI** on Windows via runtime resolution in `theme.refresh_fonts()`.
Body text is 14px — one notch larger than typical desktop defaults,
matching the friendly, oversized feel of the geometry.

## Layout & Spacing

The 4pt grid, used generously. Window margins are 28px, cards carry
16px inner padding, and gaps between major sections are 16–24px.
Breathing room is the point — nothing should feel cramped.

## Elevation & Depth

Depth comes from **surface contrast plus hairlines**:

1. **Canvas vs. Card**: Mist (#eef0f7) vs. white (#ffffff) separates
   layers without shadows.
2. **Hairline Borders**: Every card carries a 1px #e6e8f2 border so
   white tiles remain visible against white dialogs and each other.
3. **Soft Wells**: Inputs use a light gray fill (#f1f2f8) to sink below
   the card surface.

## Shapes

Very soft geometry: **16px for cards and dialogs**, **12px for inputs
and menus**, **20px for large sheets**, and **pill (999px)** for all
buttons and progress tracks. CustomTkinter auto-clamps corner radius to
half the widget's smaller dimension, so 999 renders as a perfect pill.

## Components

- **Buttons — all pills**: Primary buttons are filled Blue with white
  text. Secondary buttons are Blue Container chips with Blue text
  (sky blue chip). "全部停止" uses a soft rose chip; the add-download
  dialog has no cancel button — the window close (X) and Esc dismiss
  it. Icon buttons (✕ / ↻) are 28px and render as circles.
- **Icons**: Small glyphs use [lucide](https://lucide.dev) icons
  pre-rendered to transparent PNGs (`assets/icons/`, loaded via
  `yt_dlp_gui.icons`): folder-open on the 浏览… buttons, chevron-down
  on the format OptionMenu (stock triangle removed), chevron-down/up
  on the log toggle. 16px logical, rendered at 96px for crisp HiDPI.
- **Inputs**: Soft gray wells (#f1f2f8), 12px corners, hairline border,
  40px tall for primary URL entry.
- **Cards**: Pure white tiles, 16px corners, 1px hairline border. The
  add-download dialog is one large card holding the whole form.
- **Progress Bars**: 8px tube tracks in separator gray, filled Blue,
  pill ends. Color shifts to mint on completion, rose on error.
- **Status Dots**: 15px colored circles next to each list item —
  slate for queued, amber for parsing, Blue for downloading, mint for
  finished, rose for error.

## Do's and Don'ts

### Do:

- **Do** keep every button pill-shaped — radius 999 everywhere.
- **Do** use pastel chips for secondary actions; flat text buttons feel
  unfinished in this system.
- **Do** give everything room to breathe — 16px minimum inner padding.

### Don't:

- **Don't** use drop shadows — depth comes from mist-vs-white contrast.
- **Don't** use pure black (#000000) or pure red (#ff0000) — Ink and
  Rose are softer on purpose.
- **Don't** square anything off — if a corner is less than 12px, it
  belongs to a different design system.
