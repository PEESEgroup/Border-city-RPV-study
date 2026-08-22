# Source Data notes for Supplementary Fig. S8

Panel a reports minimum, middle and maximum modelled IRR under the policy-realized capital-support case. Residential systems are represented at 5 kW with self-consumption shares of 30%, 50% and 70%. Small-commercial systems are represented at 100 kW with shares of 50%, 70% and 90%. The 100-kW case is a sensitivity proxy for the broad observed non-residential category, not its complete project-size distribution. Singapore small-commercial export values additionally span the audited wholesale-price range. Hong Kong uses the gross feed-in-tariff capacity bands, so self-consumption does not affect its modelled revenue. Because the envelope explicitly divides generation between self-consumption and export, its middle values are not substitutions for the standardized central IRRs in the main screen.

Panel b reports the share of matched self-consumption and export scenarios in which the economic leader equals the observed building-sector PV-utilization leader. A black cell outline marks a stable economic direction, meaning that the same city leads in every matched scenario, whether or not that city is the observed PV leader.

The first six pairs are the primary sample. Detroit and Windsor are retained as a separately reported Supplementary candidate-pair sensitivity.

The envelope separates project size, sector installed-cost scaling, tariff class, export treatment, capital-support realization and self-consumption. It does not observe building-specific load profiles, demand-charge savings, financing, batteries, roof-surface geometry or historical installation conditions. Values are scenario diagnostics rather than observed project returns.

Reproduction commands from the revision root:

`python code/revision/audit_sector_economic_envelope.py`

`python code/revision/plot_supp_sector_economic_envelope.py`
