# Manuscript Section Plan

This plan follows the current structure already present in `paper/manuscript.tex` and treats that file as a container to be filled, not redesigned.

## 1. Section Structure Already Present In `paper/manuscript.tex`

- `\title{...}`
- `\author{...}`
- `\begin{abstract} ... \end{abstract}`
- `\section{Introduction}`
- `\section{Results}`
- `\section{Methods}`
- `\section{Discussions}`
- `\section{Code availability}`
- `\section{Data availability}`

## 2. What Each Section Should Accomplish

### Title
- Provide a concise, broad-interest title aligned with the central argument in `docs/manuscript_blueprint.md`.
- Emphasize cross-border rooftop PV divergence and the roles of economic returns and policy frictions.

### Abstract
- Deliver the complete paper in compressed form.
- Cover context, research question, approach, principal findings, and implication.
- Keep tone compact and restrained, consistent with `docs/journal_style.md`.

### Introduction
- Frame rooftop PV divergence as an urban and cross-border governance question rather than a simple wealth gradient.
- Motivate border-city comparison as a quasi-comparative design.
- State the gap in current literature.
- Introduce the paper’s question, contributions, and the three recurring divergence patterns.
- Preview the distinction between all-building patterns and sector-specific mechanisms.

### Results
- Present the empirical story in the same order as the blueprint narrative logic.
- First establish recurring divergence patterns across the six border-city pairs.
- Then show that overall PV gaps align more closely with returns and frictions than with wealth.
- Then unpack building-type and roof-size heterogeneity.
- Keep the section figure-driven and centered on visible evidence.

### Methods
- Explain how rooftop PV mapping, economic modeling, policy-friction coding, and pairwise comparison were carried out.
- Provide enough methodological detail for the reader to understand the construction of the evidence shown in the Results.
- Keep Figure 1 primarily as workflow support rather than a results figure.

### Discussions
- Interpret the three-pattern framework and its broader implications.
- Re-emphasize that wealth alone is an incomplete explanation.
- Distinguish revenue-side versus administrative mechanisms, and residential versus non-residential responses.
- State limitations and restrained policy implications.

### Code availability
- State where analysis and plotting scripts can be accessed.
- Keep this factual and short.

### Data availability
- State where mapped data, derived city-level files, and source data can be accessed, including any restrictions.
- Keep this factual and short.

## 3. Which Figures Belong To Each Section

### Introduction
- No figure is strictly required here.
- `Figure 1` should be the first figure mentioned.
- Use `Figure 1` briefly in the Introduction as a high-level framework figure to orient the reader to study scope, workflow, and analytical framing.
- Do not let `Figure 1` dominate the Introduction with detailed methods exposition.

### Results
- `Figure 2`
  Best for establishing recurring cross-border divergence patterns.
- `Figure 3`
  Best for linking PV utilization gaps to IRR and policy-friction differences.
- `Figure 4`
  Best for unpacking economic-return contrasts and rate-structure context.
- `Figure 5`
  Best for showing the policy-friction structure across pairs.
- `Figure 6`
  Best for sectoral and roof-size heterogeneity.

### Methods
- `Figure 1`
  Reuse `Figure 1` formally in the Methods section as the workflow and analytical-integration figure.
  The Methods section is where the components of `Figure 1` should be explained in detail.

### Discussions
- No new figure needs to be introduced here.
- Discussion should synthesize the logic established by `Figures 2-6`, especially `Figures 3`, `5`, and `6`.

## 4. What Evidence Should Be Emphasized

### Introduction
- Emphasize the comparative setting and the question the paper asks.
- Use conceptual evidence only.
- Avoid front-loading detailed quantitative results here.

### Results
- For the first results block, emphasize the directly visible within-pair PV utilization splits and rank-order patterns in `Figure 2`.
- For the second results block, emphasize the signed gap relationships in `Figure 3`, the city-level economic contrasts in `Figure 4`, and the coded friction contrasts in `Figure 5`.
- For the third results block, emphasize residential versus non-residential divergence, large-roof behavior, and building-type heterogeneity in `Figure 6`, supported by `Figure 3c` and `Figure 5`.
- Discuss `Figure 6` from the mapped ground-truth summary values in the listed input files.
- Keep `Figure 6` interpretation pair-specific and restrained; avoid turning selective pair patterns into a universal claim.
- Use exact numbers only when they are printed in the figure or clearly traceable to mapped input files already documented in `outputs/results_catalog.md`.

### Methods
- Emphasize:
  - rooftop PV mapping workflow,
  - segmentation/coverage support,
  - building-level aggregation logic,
  - PV economic indicators,
  - policy-friction codebook and matrix logic,
  - pairwise signed-gap comparison framework.

### Discussions
- Emphasize synthesis rather than repeating figure-by-figure description.
- Focus on:
  - why wealth alone is insufficient,
  - how economic returns and policy frictions jointly align with PV leadership,
  - why sector-specific policy logic matters,
  - what the six-pair framework contributes conceptually,
  - what the main limitations are.

### Code availability and Data availability
- Emphasize only access/provenance statements.
- Do not repeat scientific interpretation here.

## 5. What Should Be Left To The Supplementary Information

- Detailed segmentation benchmark reporting beyond the concise summary needed in the main Methods.
- Extended mapping coverage tables or per-city inventory details.
- Full economic-model assumptions, parameter tables, and source notes.
- Detailed policy-friction codebook and scoring rubric tables.
- Extended robustness checks, alternative specifications, and extra pair-level breakdowns.
- Variable notes, implementation details, and traceability tables that support but do not carry the central claim.
- Any extended figure or table material needed to validate the main text without overloading it.

## 6. Missing Placeholders Or Section Labels That Should Be Added

These should be added only as fill-in guides inside the existing structure, not as a redesign.

### High-priority missing placeholders
- Add an explicit abstract placeholder block inside `\begin{abstract}`.
- Add an explicit Introduction placeholder comment or marker under `\section{Introduction}`.
- Add subsection placeholders under `\section{Results}` for the three results blocks already implied by `docs/manuscript_blueprint.md`:
  - border-city rooftop PV adoption patterns,
  - economic return and policy friction patterns,
  - sectoral heterogeneity across neighboring cities.
- Add subsection placeholders under `\section{Methods}` for:
  - study area and border-city pairs,
  - orthophoto/building-footprint data,
  - rooftop PV segmentation and building-level mapping,
  - economic and policy variables,
  - comparative analysis.
- Add a Discussion placeholder under `\section{Discussions}`.
- Add short factual placeholders under `\section{Code availability}` and `\section{Data availability}`.

### Section-label issues to check
- `\section{Discussions}` should be checked against `docs/journal_style.md`, which specifies `Discussion` in singular form. `[CHECK]`
- `\section{Code availability}` and `\section{Data availability}` are currently numbered sections; if journal formatting later requires unnumbered back-matter sections, that can be handled later without changing the substantive plan. `[CHECK]`

### Figure-legend placeholders currently missing
- The current `paper/manuscript.tex` has no figure-legend block.
- A figure-legend section or placeholder block for `Figures 1-6` should be added later if this manuscript file is intended to hold submission-ready legends. `[CHECK]`

## Recommended Fill Order

1. Fill the Results subsections first, because the figure-to-claim mapping is already strongest there.
2. Fill Methods next, anchored on `Figure 1` and the mapped source files.
3. Draft the Introduction after the Results and Methods are stable.
4. Draft Discussions after the full empirical logic is in place.
5. Finish abstract, title, and availability statements last.
