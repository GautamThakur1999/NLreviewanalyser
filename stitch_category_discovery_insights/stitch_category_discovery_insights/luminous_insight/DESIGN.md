---
name: Luminous Insight
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#d1c5ae'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#9a907b'
  outline-variant: '#4e4634'
  surface-tint: '#edc13d'
  primary: '#ffebbc'
  on-primary: '#3d2e00'
  primary-container: '#f8cb46'
  on-primary-container: '#6e5600'
  inverse-primary: '#755b00'
  secondary: '#98cbff'
  on-secondary: '#003354'
  secondary-container: '#016098'
  on-secondary-container: '#b5d8ff'
  tertiary: '#ffe8dc'
  on-tertiary: '#512400'
  tertiary-container: '#ffc49f'
  on-tertiary-container: '#8e4400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe08f'
  primary-fixed-dim: '#edc13d'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#584400'
  secondary-fixed: '#cfe5ff'
  secondary-fixed-dim: '#98cbff'
  on-secondary-fixed: '#001d33'
  on-secondary-fixed-variant: '#004a77'
  tertiary-fixed: '#ffdbc7'
  tertiary-fixed-dim: '#ffb688'
  on-tertiary-fixed: '#311300'
  on-tertiary-fixed-variant: '#733600'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-margin: 24px
  gutter: 16px
  card-padding: 20px
  section-gap: 40px
---

## Brand & Style

This design system is engineered for high-density data exploration and strategic decision-making. The visual narrative balances professional utility with a modern, high-energy tech aesthetic. By utilizing a deep charcoal canvas punctuated by vibrant accents, the UI directs the user's focus toward critical performance metrics and market trends.

The style is a hybrid of **Minimalism** and **Modern Corporate**, focusing on clarity, speed, and reduced cognitive load. It evokes a sense of intelligence and precision, ensuring that complex category data feels accessible and actionable. The interface relies on structural integrity and intentional color application to maintain a premium, authoritative feel.

## Colors

The palette is optimized for long-form data analysis in low-light environments. The primary background is a deep near-black to eliminate glare, while card surfaces use a lifted charcoal to provide depth.

- **Primary Accent:** #F8CB46 (Yellow) is used sparingly for primary actions and critical highlights.
- **Data Visualization:** We move away from traditional red/green signals to ensure accessibility. 
    - **Positive/Growth:** Bright Blue (#377EB8).
    - **Negative/Risk:** High-contrast Orange (#FF7F00).
    - **Alternate/Trend:** Deep Purple (#984EA3).
- **Typography:** Pure white is reserved for high-level headings, while secondary body text uses a softer off-white (#E0E0E0) to reduce eye strain.

## Typography

The typography system uses **Inter** exclusively, leaning into its systematic and utilitarian strengths. The hierarchy is established through aggressive weight differences rather than just size. 

Headlines are tight and bold to anchor the data sections. Labels are often uppercase with slight letter spacing to differentiate them from interactive body text. For data-heavy tables, use `body-sm` to maximize information density without sacrificing legibility.

## Layout & Spacing

This design system employs a **Fluid Grid** logic with a strict 8px baseline.
- **Desktop:** 12-column grid with 24px margins. Elements should snap to column boundaries to maintain alignment in dense dashboards.
- **Tablet:** 8-column grid with 20px margins.
- **Mobile:** 4-column grid with 16px margins. 

Spacing is used to group related insights. Use larger gaps (40px+) between major category sections and tighter padding (20px) within discovery cards. Tables should utilize alternating row colors or subtle borders rather than heavy padding to keep data compact.

## Elevation & Depth

In this dark-mode environment, depth is communicated through **Tonal Layers** and subtle **Low-Contrast Outlines**.

1.  **Level 0 (Background):** #121212.
2.  **Level 1 (Cards/Surfaces):** #1E1E1E. Surfaces should use a 1px border of #2A2A2A to define edges.
3.  **Level 2 (Popovers/Modals):** #252525 with a soft, diffused black shadow (0px 8px 24px rgba(0,0,0,0.5)).

Avoid heavy drop shadows on primary cards; instead, use the value difference between the background and surface to create a "lifted" effect. For interactive elements, a subtle inner glow or outer stroke using the primary yellow can indicate focus.

## Shapes

The design system follows the **ROUND_EIGHT** philosophy. 
- **Standard Cards:** 1.5rem (24px) for `rounded-xl` to create a friendly but structured container.
- **Buttons & Inputs:** 0.5rem (8px) for `rounded-md` to maintain a professional, clickable feel.
- **Data Points:** Small charts and chips use 1rem (16px) `rounded-lg` for distinct visual separation.

The contrast between the soft outer containers (cards) and the more precise inner elements (buttons) creates a sophisticated architectural hierarchy.

## Components

- **Buttons:** Primary buttons use the #F8CB46 background with black text for maximum visibility. Secondary buttons are outlined with a 1px stroke of #E0E0E0.
- **Cards:** Use #1E1E1E surfaces. Header areas within cards should have a subtle bottom border (#2A2A2A) to separate titles from content.
- **Data Chips:** For positive trends, use a Blue (#377EB8) background at 15% opacity with solid Blue text. For negative trends, use Orange (#FF7F00) at 15% opacity with solid Orange text. 
- **Input Fields:** Backgrounds should be slightly darker than the card surface (#161616) with a 1px border that glows Primary Yellow on focus.
- **Segmented Controls:** Use a pill-shaped container with a subtle dark-grey fill. The active state should be a high-contrast white or yellow "slide-over" element.
- **Charts:** Line and bar charts should use the color-blind friendly palette. Grid lines in charts must be low-contrast (#2A2A2A) to keep the data as the hero.