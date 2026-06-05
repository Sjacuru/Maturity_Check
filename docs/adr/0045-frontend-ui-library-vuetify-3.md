# Frontend UI library — Vuetify 3

Vuetify 3 (Material Design component library for Vue 3) is the chosen UI framework for the frontend.

**Why:** The system's engineering value is in extraction, retrieval, evaluation, and provenance — not in custom UI construction. Vuetify provides mature, production-quality implementations of exactly the widgets the auditor review workflow requires: expansion panels (Ação cards), data tables (chunk evidence), file input (document upload), form controls and validation (score submission), status chips (uncertainty flag, retrieval mode), and alerts (assessment lifecycle feedback). Using Vuetify reduces the amount of frontend code the project must own and maintain.

**Considered alternative:** Tailwind CSS (utility-first, no component library). Rejected for this project: Tailwind gives layout control but requires writing every interactive component from scratch. For an internal auditor-facing tool with no branding requirements, that is engineering effort spent on infrastructure outside the system's core purpose.

**Note:** Tailwind would be the right choice if this were a public product with custom branding requirements. Vuetify is the more conservative choice for an internal academic tool.
