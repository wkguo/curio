# Curio UI design system

**Target feeling:** Duolingo × Khan Academy × a modern AI copilot. Friendly, clean, modern and educational, without being childish or enterprise-like.

## Brand

- **Mascot: Curio**, a small violet owl with a lightbulb antenna. Pure SVG + Framer Motion ([components/mascot/curio.tsx](../frontend/components/mascot/curio.tsx)).
  - Moods: `idle`, `thinking` (the bulb pulses and the eyes look up), `curious` (head tilt, raised brow), `happy`, `celebrate` (bounce, wing flaps, sparkles), `wave`.
  - Curio appears wherever the product speaks: chat bubbles, the thinking panel, insights and results.
- **Illustrations**: Microsoft Fluent 3D emoji (MIT), 123 assets at 160 px in `public/assets/emoji/`. They're referenced by key (`<Emoji name="spoon" />`), and curriculum YAML uses the same keys.
- **Type**: Nunito (400–900) for everything. Its rounded shapes feel friendly while staying readable. JetBrains Mono is used only for trace JSON.

## Color tokens (`tailwind.config.ts`)

| Token | Use |
|---|---|
| `curio-500` #7C5CFF | Primary actions, brand, the student's own chat bubbles |
| `cream` #FFF9F1 + a dotted "paper" texture | App background |
| `ink-*` | Text and borders (text never uses a series color) |
| `mint` / `sun` / `coral` | **Reserved for status**: mastered / learning / needs practice |
| `sky` | Transfer-challenge surfaces |
| Topic colors #F2703A · #3D7BF5 · #14A89A | Heat / Forces / Matter. Validated with the dataviz palette checker (worst CVD ΔE 19.9) |

Mastery status is never shown by color alone. It always pairs with an icon (✓ / half-filled circle / ! / ○ / lock) and a label.

## Components

- **Chunky "lip" buttons**: a solid bottom shadow that presses down on click (`components/ui/button.tsx`).
- **Cards**: `rounded-3xl`, a hairline border and a soft two-layer shadow (`card-base`).
- **Motion**:
  - spring-in chat bubbles, and a typing indicator paced by message length;
  - animated progress bars and rings, and count-up numbers;
  - confetti when mastery is confirmed;
  - an animated trace pipeline.
  - `prefers-reduced-motion` disables all of it.
- **Charts** (Recharts): thin marks with rounded data ends and a recessive grid. Every chart has a tooltip, and multi-series charts have legends. The heatmap uses a single-hue sequential ramp.

## Page map

| Route | Purpose |
|---|---|
| `/` | Landing: hero with an animated mini demo, chatbot-vs-Curio comparison, the 5-step loop, safety |
| `/dashboard` | Greeting, streak and XP, Continue Learning hero (✓ ◐ ○ concept list), today's goal ring, Curio insight, topics, 14-day trend, badges, recent activity |
| `/learn` | Topic picker, then the chat-style learning loop with a right panel (concept mastery, Curio insight, behind-the-scenes trace) |
| `/progress` | React Flow concept graph coloured by mastery, concept detail, bars, radar |
| `/concepts` | Myth-vs-fact flip cards and the big ideas |
| `/teacher` | Class KPIs, answer-vs-reasoning, misconceptions, activity, strategies, heatmap, traces |
| `/teacher/trace/[id]` | AI diagnosis pipeline, step inspector with JSON outputs, harness timeline, teaching conversation |

Layout: a left sidebar on desktop; a top bar plus a floating bottom tab bar on mobile (checked at 390 px).
