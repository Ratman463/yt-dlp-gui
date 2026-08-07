---
name: Neo-Esoteric Monument
colors:
  surface: '#fbf9f4'
  surface-dim: '#dbdad5'
  surface-bright: '#fbf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f4ef'
  surface-container: '#efeee9'
  surface-container-high: '#e9e8e3'
  surface-container-highest: '#e3e2de'
  on-surface: '#1b1c19'
  on-surface-variant: '#4d4545'
  inverse-surface: '#30312e'
  inverse-on-surface: '#f2f1ec'
  outline: '#7f7575'
  outline-variant: '#d0c4c4'
  surface-tint: '#615d5d'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1d1b1b'
  on-primary-container: '#878382'
  inverse-primary: '#cbc5c5'
  secondary: '#745b1d'
  on-secondary: '#ffffff'
  secondary-container: '#fedc91'
  on-secondary-container: '#785f21'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#410004'
  on-tertiary-container: '#dd5853'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e7e1e1'
  primary-fixed-dim: '#cbc5c5'
  on-primary-fixed: '#1d1b1b'
  on-primary-fixed-variant: '#494646'
  secondary-fixed: '#ffdf9a'
  secondary-fixed-dim: '#e3c37a'
  on-secondary-fixed: '#251a00'
  on-secondary-fixed-variant: '#5a4305'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#8a1b1d'
  background: '#fbf9f4'
  on-background: '#1b1c19'
  surface-variant: '#e3e2de'
  etch: '#9F2B2A'
  brass: '#fedc91'
  brass-active: '#e3c37a'
  charcoal-border: '#4d4545'
  success: '#2e7d32'
typography:
  display-serif:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  quote-editorial:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.4'
  body-main:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0.01em
  metadata-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.15em
  label-small:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.05em
spacing:
  unit: 4px
  margin-page: 64px
  gutter: 32px
  block-gap: 48px
  element-gap: 16px
rounded:
  sm: 0px
  DEFAULT: 0px
  md: 0px
  lg: 0px
  xl: 0px
  full: 0px
components:
  button-primary:
    backgroundColor: '{colors.brass}'
    textColor: '{colors.on-surface}'
    rounded: 0px
    padding: 8px 16px
  button-primary-hover:
    backgroundColor: '{colors.brass-active}'
  button-etch:
    backgroundColor: '{colors.surface-container-lowest}'
    textColor: '{colors.on-surface}'
    rounded: 0px
    padding: 8px 16px
    border: 1px solid '{colors.charcoal-border}'
  button-etch-hover:
    backgroundColor: '{colors.surface-container}'
  button-danger:
    backgroundColor: '{colors.error}'
    textColor: '{colors.on-error}'
    rounded: 0px
  input:
    backgroundColor: '{colors.surface-container-lowest}'
    textColor: '{colors.on-surface}'
    rounded: 0px
    border: 1px solid '{colors.outline}'
  input-focus:
    border: 2px solid '{colors.brass}'
  card:
    backgroundColor: '{colors.surface-container-lowest}'
    rounded: 0px
    border: 1px solid '{colors.outline}'
  progress-bar:
    backgroundColor: '{colors.outline}'
    fillColor: '{colors.brass}'
    rounded: 0px
  etch-line:
    backgroundColor: '{colors.etch}'
    height: 1px
    rounded: 0px
---

## Brand & Style

The design system is rooted in the "Minimalist Neo-Esoteric" aesthetic — a fusion of ancient monumentalism and modern editorial precision. It evokes the feeling of a rare, physical manuscript or a stone-carved archive rather than a digital interface.

The style is **Tactile and Minimalist**, rejecting standard web conventions in favor of a craftsmen-focused approach. It utilizes physical metaphors — heavy cardstock, etched metal highlights, and hard-edged shadows — to create a sense of permanence and weight.

## Colors

The palette is anchored by **Warm Alabaster** (#fbf9f4) as the primary canvas. **Rich Charcoal** (#1b1c19) provides weight for primary text and structural boundaries.

**Matte Brass** (#fedc91) is reserved for interactive highlights — buttons, progress bars, focus states. **Deep Crimson** (#9F2B2A) is used exclusively as a structural "bloodline" — 1px offset lines and state indicators to suggest depth and history without digital blurs.

## Typography

This design system uses **Newsreader** (serif) for display headlines and **Inter** (sans-serif) for all functional data and body text. Metadata and labels must utilize heavy tracking and uppercase styling to evoke architectural engravings.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy, centered on the screen like an open book. Content is organized with wide gutters and generous vertical gaps to slow the reader's pace and demand attention.

## Elevation & Depth

Depth is achieved through **Physical Offsets** rather than ambient blurs:

1. **The Etch**: Interactive cards use a 1px solid offset in Deep Crimson (#9F2B2A) — a "cut" or "stamped" look.
2. **The Inlay**: Interactive elements shift 1px on active state, simulating a physical press.
3. **Tonal Stacking**: Surfaces use thin Charcoal borders (1px) to define boundaries. No soft shadows are permitted.

## Shapes

All corners are strictly **0px**. Rectangles represent stone slabs and cut paper. The shape language is architecturally sharp — any curvature would betray the monumental intent.

## Components

- **Buttons**: Primary buttons are solid Matte Brass (#fedc91) with Charcoal text. Secondary buttons use a 1px Charcoal border with Alabaster fill.
- **Inputs**: White background with 1px Outline border. On focus, border switches to 2px Matte Brass.
- **Cards**: Pure Alabaster containers with 1px Outline borders. No shadows.
- **Progress Bars**: Alabaster track with Matte Brass fill. 0px radius.
- **Etch Lines**: 1px Deep Crimson horizontal rules used as section dividers.

## Do's and Don'ts

### Do:
- **Do** use generous whitespace. Every element should breathe.
- **Do** use uppercase Inter with heavy tracking for labels and metadata.
- **Do** use Deep Crimson only for etch lines and error states.

### Don't:
- **Don't** use rounded corners. 0px is a strict rule.
- **Don't** use drop shadows. Depth comes from borders and tonal stacking.
- **Don't** use bright or saturated colors beyond Brass and Crimson.