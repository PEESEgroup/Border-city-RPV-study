## Repository map
- `docs/manuscript_blueprint.md`: paper storyline, section logic, candidate titles
- `docs/figure_map.md`: figure purpose, panel meaning, input files, key message
- `docs/variable_dictionary.md`: variable definitions, units, and direction
- `docs/journal_style.md`: target journal style and caption conventions
- `data/`: final result files
- `scripts/`: read results and plotting scripts
- `figures/main/`: final main-text figures
- `figures/supplement/`: final supplementary figures
- `paper/`: manuscript and SI drafts
- `outputs/`: agent-generated intermediate outputs and audits

## Manuscript skeleton
- Use `paper/manuscript.tex` as the primary manuscript skeleton and structure source of truth.
- Use `paper/supplementary.tex` as the primary SI skeleton and structure source of truth.

When drafting manuscript text:
- first read the skeleton to understand where the new text belongs,
- preserve the existing section and subsection structure,
- use `docs/manuscript_blueprint.md` for section goals, narrative logic, and key points,
- use `docs/journal_style.md` for tone and journal-style conventions,
- use `docs/figure_map.md`, the actual figure images, listed input files, and scripts as supporting evidence,
- write text that fits directly into the LaTeX manuscript,
- do not restructure the manuscript unless explicitly asked.

Treat the manuscript skeleton as a container to be filled, not a document to be redesigned.

## Core writing principle: section-led, evidence-supported narrative
The manuscript must follow a Nature-style narrative logic: each section should be organized around a scientific question, key message, or analytical goal, not around a list of figures.

Figures are evidence. They support the section-level conclusion; they should not determine the paragraph structure by themselves.

For every Results or Discussion section:
1. Identify the section goal from `docs/manuscript_blueprint.md`.
2. Identify the main claim or conclusion the section needs to establish.
3. Use the relevant figure(s), tables, data files, and scripts as evidence for that claim.
4. Write paragraphs in a claim-first order:
   - topic sentence: state the analytical point or scientific conclusion,
   - evidence sentence(s): cite the figure, panel, table, or data that supports the point,
   - interpretation sentence: explain why the pattern matters for the paper's central argument.

Do not write the Results section as a figure-by-figure tour.

Bad pattern:
> Figure 2 shows the rooftop PV distribution in all studied cities. Figure 2a presents the PV maps, while Figure 2b shows the installation density.

Preferred pattern:
> Rooftop PV adoption differs sharply across neighboring border cities despite their geographic proximity. These differences are visible both in city-scale PV distributions and in building-level installation density, where several city pairs show asymmetric clustering across the border (Fig. 2a,b).

## Paragraph-level rules for Nature-style Results writing
- In manuscript prose, refer to main-text figures as `Fig. X` and panel references as `Fig. Xa,b`.
- Refer to supplementary figures as `Supplementary Fig. S1` or `Supplementary Fig. S1a,b`.
- Do not use `Figure X` in running manuscript text; reserve full `Figure X.` for captions only if needed by the journal style.
- Do not start most paragraphs with `Figure`, `Fig.`, `Panel`, or `Table`.
- Avoid repetitive openings such as `Figure X shows`, `Figure X presents`, `Figure X illustrates`, or `As shown in Figure X`.
- Start paragraphs with the scientific point, not the display item.
- Mention figures only after the claim has been stated.
- Use figures as citations or evidence, for example: `(Fig. 2a,b)`, `as supported by Fig. 3c`, or `consistent with Supplementary Fig. S2`.
- If a figure has multiple panels, discuss the panel only when the panel provides specific evidence for the claim.
- Do not describe every visual element unless it is needed to support the argument.
- End paragraphs with interpretation, implication, or transition, not just a figure reference.

Paragraph template:
```text
[Claim or analytical point]. [Specific evidence, with figure/panel reference]. [Quantitative or comparative detail if available]. [Interpretation: why this supports the paper's broader argument].
```

### Paragraph length and balance rules:
1. Keep paragraph lengths moderately balanced across each Results subsection.
2. Avoid very short paragraphs with only one or two sentences unless they are used as a clear transition.
3. Avoid overly long paragraphs that combine multiple analytical points.
4. As a guideline, most Results paragraphs should be about 100–160 words, usually 4–6 sentences.
5. Each paragraph should develop one main analytical point:
   - one topic sentence,
   - two to three evidence or comparison sentences,
   - one interpretation or transition sentence.
6. Do not make all paragraphs mechanically identical in length, but avoid large imbalance where one paragraph is 50 words and the next is 300 words.
7. If a paragraph contains multiple claims, split it into two balanced paragraphs.
8. If two neighboring paragraphs are too short and address the same claim, merge them into one coherent paragraph.
9. Maintain a concise Nature-style rhythm: dense enough to carry evidence, but not so long that the claim becomes buried.


## Results section workflow
When drafting or revising a Results section:

1. Read the corresponding section in `docs/manuscript_blueprint.md`.
   Extract:
   - section goal,
   - key points,
   - central claim,
   - supporting figures and tables.

2. Read the relevant part of `paper/manuscript.tex`.
   Determine:
   - where the new text belongs,
   - what has already been stated,
   - which claims still need evidence.

3. Inspect the relevant figure images.
   Determine:
   - what is visually present,
   - panel labels and layout,
   - main comparisons or patterns,
   - axes, legends, colors, symbols, and annotations,
   - what a reader can directly learn from the figure alone.

4. Read `docs/figure_map.md`.
   Use it to confirm:
   - the figure purpose,
   - panel meanings,
   - intended terminology,
   - key message,
   - input files and variables.

5. Read the input files and scripts listed for each figure.
   Use them only to:
   - verify quantitative claims,
   - recover exact variable names and units,
   - clarify data provenance,
   - confirm data processing steps, transformations, aggregations, and merges,
   - ensure that the manuscript description matches the implemented analysis.

6. Draft the section around the section-level conclusion.
   Use the figures as support, not as the organizing skeleton.

7. Before finalizing, check that:
   - the first sentence of each paragraph is a claim or transition,
   - no consecutive paragraphs begin with `Figure` or `Fig.`,
   - all figure references in manuscript prose use the `Fig. X` format,
   - every figure reference supports a specific claim,
   - all quantitative statements are traceable to a figure, table, input file, or script,
   - the section ends by connecting the result to the paper's central argument.

## Figure caption workflow
Figure captions are different from Results prose. Captions may be more figure-centered because their job is to help readers decode the visual display.

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

4. Write captions in a concise Nature-style structure:
   - opening sentence: the main message of the figure,
   - panel descriptions: what each panel shows,
   - data/method notes: only what is needed to interpret the figure,
   - abbreviation/unit clarification where needed.

5. Apply caption emphasis formatting:
   - bold the first sentence of the full caption; this sentence should state the figure's main takeaway,
   - for each panel description, bold the first sentence that gives the panel's key point,
   - keep any follow-up explanatory detail for that panel in normal text,
   - use this as a formatting rule, not as a license to make captions overly long.

Example caption pattern:
```text
**Cross-border rooftop PV adoption diverges through distinct economic-return and policy-friction patterns.**
a, **City-pair PV utilization differs markedly across neighboring border cities.** The map compares building-level rooftop PV utilization across the six city pairs.
b, **Return and friction conditions jointly structure these cross-border gaps.** Paired indicators summarize economic return and policy-friction differences for each city pair.
```

6. Use `Fig. X` style in manuscript text, but in captions keep the focus on what the figure shows rather than self-referencing the figure number in the opening sentence.

7. If the image and `docs/figure_map.md` do not fully match, do not guess.
   Explicitly flag the inconsistency and use `[CHECK PANEL MAPPING]` or `[CHECK FIGURE MESSAGE]`.

8. Do not write captions from `docs/figure_map.md` alone without inspecting the actual figure.
9. Do not infer quantitative claims unless they are clearly visible in the figure or traceable to repository data.

## Source priority
For manuscript prose, use sources in this order:

1. `docs/manuscript_blueprint.md`: section-level goal, narrative logic, and central claim
2. figure image itself: what is actually visible to the reader
3. `docs/figure_map.md`: figure purpose, panel meaning, terminology, input files
4. listed input files: quantitative support, variable names, units, provenance
5. listed scripts: analysis logic, transformations, aggregation, model assumptions
6. `docs/journal_style.md`: tone, structure, caption style

For figure captions, use sources in this order:

1. figure image itself: what is actually visible to the reader
2. `docs/figure_map.md`: figure purpose, panel meaning, terminology, input files
3. listed input files and scripts: quantitative support and provenance
4. `docs/journal_style.md`: caption tone and format

## Supplementary Information workflow
If additional supporting evidence is needed for a claim, or if explicitly instructed, use `paper/supplementary.tex` as the source-of-truth supplementary skeleton.

Use `paper/supplementary.tex` for:
- supplementary methods details,
- robustness checks,
- alternative specifications,
- extended results,
- supplementary figures and tables,
- variable or implementation notes that support the main manuscript.

Rules:
- keep the structure and writing style consistent with the main manuscript skeleton,
- use the Supplementary Information only to support or validate claims made in the main paper,
- do not introduce a new central claim in the Supplementary Information,
- do not move essential main-text results into the Supplementary Information unless explicitly asked,
- preserve the existing section structure of `paper/supplementary.tex`,
- if uncertain, insert `[CHECK]` instead of guessing.

## Claim and evidence discipline
- Every strong claim in the main text must be supported by at least one of the following:
  - a main-text figure,
  - a supplementary figure or table,
  - an input data file,
  - an analysis script,
  - a clearly stated method or assumption.
- Do not introduce claims that are not visually or quantitatively supported.
- Do not overstate causality from cross-sectional comparisons.
- Use cautious language where appropriate: `suggests`, `is consistent with`, `indicates`, `is associated with`.
- Reserve stronger causal language only for mechanisms directly established by the analysis design.

## Consistency and alignment checks
Before finalizing any manuscript or SI edit, check for:
- figure references that match the actual figure numbering in `paper/manuscript.tex`,
- manuscript figure references consistently use the `Fig. X` style,
- panel references that match visible panel labels,
- terminology consistency with `docs/variable_dictionary.md`,
- units consistency across text, figures, captions, and tables,
- caption formatting follows the rule that the main caption sentence and each panel's first key sentence are bolded,
- alignment between claims, figures, data files, and scripts,
- no unsupported statements introduced for narrative fluency.

If the figure image, `docs/figure_map.md`, input files, and scripts do not fully match, do not guess. Explicitly flag the issue with `[CHECK FIGURE ALIGNMENT]`.

## File safety
- Never overwrite raw data or final CSV files.
- Never edit files under `data/`.
- Prefer writing new outputs to `outputs/`.
- Only edit manuscript files under `paper/` when explicitly asked.
- Save any new tables or results to `outputs/`.
- Save audit reports to `outputs/audit_reports/`.
