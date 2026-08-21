# Source Data notes for Supplementary Fig. S4

Supplementary Fig. S4 contains the six primary border-city pairs only. Detroit and Windsor are excluded from both panels and remain in the dedicated candidate-pair sensitivity section.

Panel a reports the eight documented-rule component scores for 12 cities. Components A to D describe export compensation, export constraints, settlement complexity and policy uncertainty. Components E to H describe small-system approval, building or planning approval, grid-study or fee requirements and professional-credential requirements. Scores are ordinal screening values from 0 to 3, with higher values indicating greater documented friction. Revenue, administrative and total index sums are retained in `Fig_S_policy_a.csv`; the sums are not interval-scale measurements.

Within-pair lower-friction labels use the fixed city order. C1 denotes the first-listed city, C2 denotes the second-listed city and Tie denotes equal scores.

Panel b uses the same fixed order. Component advantage is the second-listed city's component score minus the first-listed city's score, so positive values indicate lower documented friction for the first-listed city. Segment-specific PV advantage is first-listed minus second-listed PV utilization in percentage points. Signed alignment contribution is their product. Positive values indicate that lower documented friction and higher observed utilization occur on the same side of a pair. Point area represents the absolute contribution.

Every factor-segment cell retains all six primary-pair comparisons, including zero component advantages. Residential and non-residential weights sum the absolute component advantage only across same-sign pair comparisons for each segment, then normalize the two segment totals within factor.

The figure is descriptive. Written rules do not measure queues, approval duration, customer service, enforcement consistency, informal institutional capacity or installer experience. Grid studies, interconnection reviews and low midday export values may reflect high renewable penetration, deployment maturity or grid-management requirements. The figure does not estimate mediation, deployment pathways, policy effects or causal mechanisms.

Reproduction command:

```bash
python code/revision/plot_supp_policy_documented_components.py
```

Frozen inputs:

- `evidence/v1_verified_data/policy_friction_14cities.csv`
- `evidence/v1_verified_data/city_pv_metrics_14cities.csv`

The numerical checks are stored in `Source_Data/source_data_checks_fig_s_policy.json`.

The final supplementary composite preserves the exact Illustrator composition and embedded Myriad Pro typography of the former main Figure 5. The revision script regenerates both numerical panels from the frozen inputs, exports a reconstructed vector composite for audit and then copies the locked style master to the submission filename. This separates numerical reproducibility from manual figure composition while preventing an unintended change in the established Nature figure style.
