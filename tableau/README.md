# Tableau Executive Dashboard — Presentation Layer

## Architectural Separation

- **MySQL owns validated analytical logic:** cohort medians, descending ranks, endpoint deltas, and low-income vs. total-population changes are computed once inside the five presentation views in `sql/07_tableau_views.sql`.
- **Tableau owns decision communication:** the executive dashboard reads directly from those five views without duplicating median, rank, or ratio formulas inside Tableau calculated fields.

## Single Executive Dashboard Design

The presentation layer is intentionally limited to **one fixed-layout desktop executive dashboard** (`assets/energiewende_executive_dashboard.png`) to keep stakeholder communication focused and scannable:

| Row | Left Card | Right Card | MySQL Source Views |
|---|---|---|---|
| **Row 1: Structural progress** | Renewable Electricity Transition, 2013–2023 (`25.3% → 51.9%`) | Generation Concentration, 2013–2023 (`74.0% → 57.1%`) | `vw_tableau_de_transition` |
| **Row 2: Competitive context & affordability** | 2023 Generation Concentration vs. Peer-Group Median (`-6.3 pp`, `-2.3 pp`, `+15.0 pp`) | Electricity Affordability Under Stress, 2021–2023 (`+26.7%`, `+85.4%`, `-22.7 pp`) | `vw_tableau_concentration_benchmark`, `vw_tableau_affordability_stress` |
| **Row 3: Social resilience & metric caution** | Household Energy Stress, 2021–2023 (`+4.9 pp` vs `+6.5 pp`; `+1.7 pp` vs `+2.8 pp`) | Why Gas Retailer Density Can Mislead, 2021–2023 (`-0.6%`, `-20.9%`, `+25.7%`) | `vw_tableau_social_resilience`, `vw_tableau_gas_density_caution` |

### Color Intention
- **Blue:** structural trends, broad peer comparisons, underlying drivers, total population.
- **Orange:** results requiring executive attention, benchmark exceptions (Big-6), low-income vulnerability, and apparent KPI improvements driven by a shrinking denominator.
- Colors signal analytical focus rather than moral value judgments.

## Reproducing the Connection

1. Execute `sql/00_create_database.sql` through `sql/07_tableau_views.sql` against a local MySQL 8.0+ server.
2. In Tableau Desktop, connect to MySQL (`germany_energiewende`) using your local credentials (never commit credentials or DSN passwords to Git).
3. Add the five `vw_tableau_*` views as separate data sources (one view per analytical block) so grain differences (11-year series vs. 3-cohort summary vs. 4-row stress test) never cause accidental cross-joins.

> **Workbook availability note:** A portable `.twb`/`.twbx` workbook is not committed because the Tableau workbook was connected to a local MySQL instance. Only the exported dashboard image (`assets/energiewende_executive_dashboard.png`) and the five reproducible MySQL views (`sql/07_tableau_views.sql`) are tracked in version control.
