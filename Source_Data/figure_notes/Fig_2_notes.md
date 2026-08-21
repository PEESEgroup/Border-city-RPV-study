# Fig. 2 Source Data and production notes

## Scope

Fig. 2 retains the six primary border-city pairs. Detroit--Windsor remains a supplementary candidate-pair sensitivity case and is absent from both panels.

## Panel a

Panel a preserves the original all-building, residential and non-residential dumbbell design, fixed pair order, pair colors, numeric labels and filled/open city encoding. All shaded pattern blocks and their group headings have been removed. The x axis reports mapped rooftop PV area divided by building-footprint area, expressed as a percentage.

The panel is generated from the boundary-audited city metrics in `evidence/v1_verified_data/city_pv_metrics_14cities.csv`. San Diego therefore appears at 2.56% for all buildings, 2.58% for residential buildings and 2.55% for non-residential buildings. Monaco--Nice carries a dagger because Monaco has a small building denominator. The corresponding counts are reported in the caption and Supplementary Table S1 rather than as a long in-panel annotation.

## Panel b

Panel b replaces the original income, PV, IRR and policy rank trajectory with an overlapping-attribute matrix. It reports the all-building, residential and non-residential leader explicitly, followed by two independent summaries: same-side versus split sector leadership, and aligned versus reversed income ordering. IRR and policy friction are excluded because they are contextual diagnostics rather than definitions of the deployment attributes.

No row blocks or background groups classify the pairs into mutually exclusive patterns. Hong Kong--Shenzhen and Monaco--Nice can therefore be read simultaneously as split sector-leadership cases and income-reversed cases.

## Production status

Panels a and b are now generated together as `figures/main/revision/fig_2.pdf` and a 300-dpi PNG preview. They share the same pair-centre y coordinates, one filled/open city-marker legend and one Monaco small-denominator annotation. SVG export has been discontinued. Final Fig. 2 lock still requires visual approval, manuscript linkage and synchronization of the Results text and caption.

Panel labels use regular Myriad Pro glyphs in the `a,` and `b,` format. Because Myriad Pro is not installed as a system font in the execution environment, the labels are rendered at high resolution from the embedded Myriad Pro labels in the approved revised Fig. 1 and stored under `figures/assets/revision/`. The labels are positioned at the left content edge of their respective panels. Panel b uses no table frame or internal rule lines. Two neutral grey fills distinguish the two possible values within each column: first-listed, same-side or aligned values use the darker grey, while second-listed, split or reversed values use the lighter grey.

The panel-b column headings use regular-weight x tick labels below the matrix, aligned vertically with the panel-a x tick labels and matching the original Fig. 2 orientation. The shared first-listed/second-listed marker legend is arranged in two rows inside the lower-right corner of panel a. The Monaco small-denominator note is split over two lines, aligned with the left edge below Nice and remains above the panel-a x-axis label. The upper y margin is reduced and the `a,` and `b,` identifiers are positioned lower within that margin.

## Final lock

Fig. 2 is locked for manuscript integration. The main-text figure link, Results subsection and caption now describe sector leadership and income ordering as overlapping attributes. Supplementary Table S1 has been synchronized to the same boundary-audited city metrics, including San Diego at 2.56%, 2.58% and 2.55% for all buildings, residential buildings and non-residential buildings, respectively. The aggregation sensitivity table now uses same-side and split sector attributes rather than mutually exclusive pattern labels.
