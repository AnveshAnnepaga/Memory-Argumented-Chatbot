---
name: Antigravity AI Design System
colors:
  surface: '#0f1321'
  surface-dim: '#0f1321'
  surface-bright: '#353849'
  surface-container-lowest: '#0a0d1c'
  surface-container-low: '#171b2a'
  surface-container: '#1b1f2e'
  surface-container-high: '#262939'
  surface-container-highest: '#303444'
  on-surface: '#dfe1f6'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#dfe1f6'
  inverse-on-surface: '#2c303f'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#d2bbff'
  on-secondary: '#3f008e'
  secondary-container: '#6001d1'
  on-secondary-container: '#c9aeff'
  tertiary: '#a8ffd2'
  on-tertiary: '#003824'
  tertiary-container: '#5be9ad'
  on-tertiary-container: '#006645'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bbff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5a00c6'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f1321'
  on-background: '#dfe1f6'
  surface-variant: '#303444'
typography:
  display-lg:
    fontFamily: Inter Tight
    fontSize: 64px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter Tight
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter Tight
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Inter Tight
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  mono-code:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  2xl: 64px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style
This design system embodies the intersection of advanced computational intelligence and enterprise-grade stability. The brand personality is "The Invisible Architect"—powerful, weightless, yet profoundly structured. It targets CTOs, lead engineers, and enterprise architects who require a tool that feels like a sophisticated extension of their cognitive workflow.

The visual style is a fusion of **Corporate Modernism** and **Refined Glassmorphism**. It utilizes depth through translucency and backdrop blurs to simulate the "antigravity" concept—elements feel suspended in a high-tech void rather than anchored to a heavy grid. The emotional response is one of calm authority, precision, and futuristic capability, avoiding "gamer" aesthetics in favor of professional, high-performance tooling.

## Colors
The palette is built on a high-contrast foundation to ensure absolute legibility for data-heavy enterprise tasks. In dark mode, the **Cyan Primary** acts as the "glow" of intelligence, while the **Violet Secondary** provides depth and sophisticated accents. 

Light mode shifts to a more clinical, paper-white aesthetic while maintaining the vibrancy of the primary accents. Use the "Elevated" color for cards and containers that sit atop the "Base" canvas. Glass effects should be applied sparingly to top-level navigation, modals, and floating panels to maintain the sense of layering without sacrificing performance or accessibility.

## Typography
The system uses **Inter Tight** for headings to achieve a more compact, geometric look that feels engineered and modern. For body text, standard **Inter** is utilized for its exceptional legibility in dense data environments. 

For technical documentation and AI reasoning outputs, **JetBrains Mono** is introduced to provide clear distinction between natural language and machine-generated data. Maintain tight tracking on large displays and generous line-heights for body text to ensure long-form reading comfort during complex knowledge analysis.

## Layout & Spacing
The layout follows a **Fluid Grid** philosophy using a 12-column system. It prioritizes vertical rhythm and visual "breathability." 

- **Desktop:** 12 columns, 24px gutters, 48px outside margins. Large hero panels span 12 columns, while secondary content panels typically occupy 4 or 8 columns.
- **Tablet:** 8 columns, 16px gutters, 24px margins.
- **Mobile:** 4 columns, 16px gutters, 16px margins.

Spacing is strictly based on a 4px baseline unit. Navigation is typically sidebar-oriented to accommodate complex application hierarchies, with a glassmorphic top-bar for global actions and search.

## Elevation & Depth
Elevation is expressed through **Glassmorphism** and **Tonal Layering** rather than traditional heavy shadows.

- **Level 0 (Base):** The #050816 background.
- **Level 1 (Surface):** Solid #0A0F24 with a 1px border of `glass_border`. Used for sidebars and secondary containers.
- **Level 2 (Floating):** Glassmorphic surface (`glass_surface`) with 20px backdrop blur and a subtle 1px border. Used for cards and main workspace panels.
- **Level 3 (Overlay):** Increased blur (40px) with a soft ambient shadow (0px 20px 40px rgba(0,0,0,0.4)). Used for modals and dropdown menus.

Lighting should always feel as if it originates from the top-center, creating extremely thin 1px "inner glows" on the top edges of elevated cards.

## Shapes
The shape language balances modern approachability with professional structure.
- **Standard UI Elements:** (Buttons, Inputs, Chips) use a **0.5rem (8px)** radius.
- **Standard Cards:** Use a **0.75rem (12px)** radius to create a sturdy, contained feel.
- **Hero & Command Panels:** Use a **1.5rem (24px)** radius for high-impact areas that define the "Antigravity" aesthetic.

All borders should be 1px in width, utilizing the `glass_border` variable to ensure they remain subtle and don't create unnecessary visual noise.

## Components
- **Buttons:** Primary buttons use a solid Cyan fill with dark text. Secondary buttons use a ghost style (1px border) with Cyan text. The "Danger" and "Success" variants follow the same logic.
- **Input Fields:** Dark surfaces with a subtle border. On focus, the border glows Cyan with a 2px outer ring at 20% opacity.
- **Chips/Badges:** Small, 8px rounded elements with a 10% opacity fill of their respective color (e.g., Success chip has 10% emerald background and solid emerald text).
- **Cards:** Glassmorphic by default in the main workspace. For data lists, use simple tonal separation (alternating #050816 and #0A0F24).
- **AI Reasoning Feed:** A specialized vertical list component. Uses a left-aligned violet accent line to denote AI-generated content, with "Inter Mono" for code blocks.
- **Knowledge Nodes:** Circular icons for data source representation, using secondary (Violet) gradients to imply depth and complexity.
- **Progress Bars:** Thin, 4px height, with a glowing Cyan head to indicate "active processing" motion.