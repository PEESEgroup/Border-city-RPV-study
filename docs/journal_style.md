# Journal Style

## Target journal style
The manuscript should be written in a style aligned with Nature Cities Articles.

## Structure
- Concise title with broad appeal
- Short abstract
- Main text organized as:
  - Introduction
  - Results
  - Methods
  - Discussion
- Use topical subheadings in Results, Discussion, and Methods


## Tone
- Broad interdisciplinary readability
- Compact, high-information-density writing
- Strong narrative logic
- Restrained interpretation
- No exaggerated causal claims

## Figure legends
- Nature-style legends
- Begin with a brief whole-figure title
- Then explain panels a, b, c in sequence
- Legends should be self-contained and interpretable on their own
- Include the main finding supported by the figure
- Define abbreviations, symbols, colors, and error bars when needed
- Avoid detailed methods in legends
- Aim for concise but informative legends, preferably within ~300 words

## Figure caption workflow
When drafting or revising figure captions:

1. First inspect and understand the figure image itself, including:
   - panel layout,
   - panel labels (a, b, c, ...),
   - visual encodings,
   - titles, legends, axes, colors, symbols, and annotations,
   - the main pattern visible in the figure.

2. Then read `docs/figure_map.md` to identify:
   - the intended purpose of the figure,
   - the meaning of each panel,
   - the input data source(s),
   - the variables used,
   - the key message the figure is supposed to support.

3. Use both sources together:
   - use the figure image to understand what is visually shown,
   - use `docs/figure_map.md` to confirm scientific intent, terminology, and data provenance.

4. If the image and `docs/figure_map.md` do not fully match, do not guess.
   Explicitly flag the inconsistency and use `[CHECK PANEL MAPPING]` or `[CHECK FIGURE MESSAGE]`.

5. Do not write captions from `docs/figure_map.md` alone without inspecting the actual figure.
6. Do not infer quantitative claims unless they are clearly visible in the figure or traceable to repository data.

## Non-negotiable rules
- No invented numbers
- No unsupported claims
- All quantitative claims must be traceable
- Use [CHECK] when evidence is uncertain