---
name: Culinary Intelligence System
colors:
  surface: '#131317'
  surface-dim: '#131317'
  surface-bright: '#39393d'
  surface-container-lowest: '#0e0e12'
  surface-container-low: '#1b1b1f'
  surface-container: '#1f1f23'
  surface-container-high: '#2a292e'
  surface-container-highest: '#353439'
  on-surface: '#e4e1e7'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e4e1e7'
  inverse-on-surface: '#303034'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#ffb955'
  on-secondary: '#452b00'
  secondary-container: '#dc9100'
  on-secondary-container: '#4f3100'
  tertiary: '#4ae176'
  on-tertiary: '#003915'
  tertiary-container: '#00a74b'
  on-tertiary-container: '#003111'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#ffddb4'
  secondary-fixed-dim: '#ffb955'
  on-secondary-fixed: '#291800'
  on-secondary-fixed-variant: '#633f00'
  tertiary-fixed: '#6bff8f'
  tertiary-fixed-dim: '#4ae176'
  on-tertiary-fixed: '#002109'
  on-tertiary-fixed-variant: '#005321'
  background: '#131317'
  on-background: '#e4e1e7'
  surface-variant: '#353439'
typography:
  display-xl:
    fontFamily: Outfit
    fontSize: 64px
    fontWeight: '800'
    lineHeight: 72px
    letterSpacing: -0.04em
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-lg:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Outfit
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Outfit
    fontSize: 14px
    fontWeight: '300'
    lineHeight: 20px
  label-md:
    fontFamily: Outfit
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
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

This design system establishes a premium, immersive environment for high-end AI-driven food discovery. The aesthetic is rooted in **Dark Glassmorphism**, prioritizing depth, transparency, and vibrant focal points against a cinematic deep-charcoal backdrop. 

The target audience is tech-savvy food enthusiasts who value speed, precision, and a curated, high-quality experience. The UI should evoke a sense of "digital concierge" expertise—sophisticated, responsive, and visually appetizing. By combining atmospheric background motion (floating orbs and subtle drifts) with razor-sharp typography, the system balances futuristic technology with the warmth of culinary culture.

## Colors

The palette is anchored by a deep charcoal background to ensure high-contrast legibility and modern appeal. 

- **Primary Accent (#e23744):** Reserved for high-action touchpoints and brand identification. It is often accompanied by an **Accent Glow** to simulate depth and light emission.
- **Gold Accent (#f5a623):** Specifically utilized for prestige markers, such as "Rank #1" status and high-tier ratings.
- **Success Green (#22c55e):** Used for financial/cost indicators and affirmative system feedback.
- **Glass Surfaces:** Semi-transparent layers use `rgba(255, 255, 255, 0.05)` combined with a `20px` backdrop blur to maintain legibility over moving background elements.

## Typography

The typography system leverages **Outfit** for its geometric clarity and modern proportions. 

- **Display Text:** Large headings utilize the "Black" (800) weight with tight negative tracking to create a high-impact, editorial feel. 
- **Hierarchy:** Section headers use the "SemiBold" (600) weight to provide clear structural breaks.
- **Body & Captions:** Light (300) and Regular (400) weights are used for descriptive content to maintain an airy, sophisticated readability. 
- **Accessibility:** Ensure that body text never falls below 14px to maintain legibility against the dark, blurred background layers.

## Layout & Spacing

The layout philosophy uses a **Fluid Grid** model with generous safe areas to highlight glassmorphic containers.

- **Desktop:** A 12-column grid with 64px outer margins. Content is often centered in a 1200px max-width container to maintain focus.
- **Mobile:** A 4-column grid with 16px margins.
- **Rhythm:** Spacing follows an 8px base unit. Use 24px (lg) for internal padding of cards and 40px (xl) for vertical section breathing room.
- **Floating Orbs:** Background decorative elements should be placed on a separate z-index layer behind the content, moving slowly with CSS animations or parallax scrolling.

## Elevation & Depth

Depth is conveyed through **refraction and light**, rather than traditional shadows.

- **Tier 1 (Base):** Deep Charcoal (#0f0f13) with animated "food drift" elements.
- **Tier 2 (Cards):** Glassmorphic surfaces with `20px` backdrop-filter blur and `rgba(255,255,255,0.09)` thin borders.
- **Tier 3 (Modals/Panels):** Higher opacity glass with a soft `0 20px 40px rgba(0,0,0,0.4)` shadow to separate it from underlying cards.
- **Interaction Glow:** Active states on primary buttons should emit a `15px` outer glow using the Primary Accent color at 35% opacity.

## Shapes

The shape language is smooth and approachable, using large radii to soften the high-tech aesthetic.

- **Large Panels:** Use 24px (rounded-xl) for main content areas and large modal containers.
- **Cards & Inputs:** Use 12px (rounded-lg) for standard restaurant cards, search bars, and input fields.
- **Buttons:** Fully rounded (pill-shaped) for primary actions to distinguish them from structural UI components.

## Components

- **Primary Buttons:** Pill-shaped, Primary Red (#e23744) background, white 600-weight text. Includes a soft red glow on hover.
- **AI Chat Input:** A 12px rounded glassmorphic bar with a subtle `1px` border. The "send" button should be a simple red circle icon.
- **Restaurant Cards:** 12px rounded corners, glass background, with a high-quality food image at the top. The "Gold Accent" is used for the rating star and "Top 1" badge.
- **Price Badges:** Small, Success Green (#22c55e) text with a low-opacity green background tint, used to indicate "Value for Money" or specific price tiers.
- **Chips/Filters:** 300-weight text, 12px rounded corners, using the `secondary-bg` color. On selection, they switch to Primary Red.
- **Lists:** Clean, borderless rows separated by a `1px` horizontal line of `rgba(255,255,255,0.05)`.