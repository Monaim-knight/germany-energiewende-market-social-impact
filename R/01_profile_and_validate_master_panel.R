# ============================================================
# Germany's Energiewende (2013-2023)
# Risk-Driven Panel Profiling & Validation in R
#
# Run from the repository root:
#   Rscript R/01_profile_and_validate_master_panel.R
#
# Required packages: readr, dplyr, stringr, tibble, purrr
# (install once interactively if missing:
#  install.packages(c("readr", "dplyr", "stringr", "tibble", "purrr")))
# ============================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(purrr)
})

# ============================================================
# Step 1 - Load validated master panel and inspect structure
# ============================================================

panel_path <- file.path("data", "processed", "master_panel.csv")
if (!file.exists(panel_path)) {
  stop("Expected input file not found at relative path: ", panel_path)
}

master_panel <- read_csv(panel_path, show_col_types = FALSE)

cat("Dimensions:", nrow(master_panel), "rows x", ncol(master_panel), "columns\n")
print(names(master_panel))
str(master_panel)

# ============================================================
# Step 2 - Identify and validate the dataset grain
# Proposed grain: one row per economy per year
# Candidate primary key: (geo, year)
# ============================================================

# 2.1 Check missing values in the candidate key
missing_key_values <- master_panel |>
  filter(is.na(geo) | is.na(year))
stopifnot(nrow(missing_key_values) == 0)

# 2.2 Check duplicate geo-year combinations
duplicate_geo_year <- master_panel |>
  count(geo, year, name = "row_count") |>
  filter(row_count > 1) |>
  arrange(desc(row_count), geo, year)
stopifnot(nrow(duplicate_geo_year) == 0)

# 2.3 Compare total rows with distinct geo-year combinations
key_summary <- master_panel |>
  summarise(
    total_rows = n(),
    distinct_geo_year = n_distinct(paste(geo, year, sep = "_")),
    duplicate_rows = total_rows - distinct_geo_year
  )
print(key_summary)
stopifnot(key_summary$total_rows == 396, key_summary$duplicate_rows == 0)

# 2.4 Check overall year range and integer status
year_summary <- master_panel |>
  summarise(
    minimum_year = min(year, na.rm = TRUE),
    maximum_year = max(year, na.rm = TRUE),
    distinct_years = n_distinct(year),
    non_integer_years = sum(year != floor(year), na.rm = TRUE)
  )
print(year_summary)
stopifnot(
  year_summary$minimum_year == 2013,
  year_summary$maximum_year == 2023,
  year_summary$distinct_years == 11,
  year_summary$non_integer_years == 0
)

# 2.5 Check number of economies
economy_summary <- master_panel |>
  summarise(
    distinct_geo_codes = n_distinct(geo),
    distinct_country_names = n_distinct(country_name)
  )
print(economy_summary)
stopifnot(
  economy_summary$distinct_geo_codes == 36,
  economy_summary$distinct_country_names == 36
)

# 2.6-2.7 Confirm balanced 2013-2023 coverage for every economy
country_year_coverage <- master_panel |>
  group_by(geo, country_name) |>
  summarise(
    first_year = min(year, na.rm = TRUE),
    last_year = max(year, na.rm = TRUE),
    observed_years = n_distinct(year),
    .groups = "drop"
  ) |>
  arrange(observed_years, geo)

incomplete_country_coverage <- country_year_coverage |>
  filter(
    first_year != 2013 |
      last_year != 2023 |
      observed_years != 11
  )
stopifnot(nrow(incomplete_country_coverage) == 0)

# ============================================================
# Step 3 - Validate identifiers and bidirectional country mapping
# ============================================================

# 3.1 Confirm candidate-key columns are complete and non-blank
missing_key_summary <- master_panel |>
  summarise(
    missing_geo = sum(is.na(geo)),
    blank_geo = sum(is.na(geo) | str_trim(geo) == ""),
    missing_year = sum(is.na(year))
  )
print(missing_key_summary)
stopifnot(
  missing_key_summary$missing_geo == 0,
  missing_key_summary$blank_geo == 0,
  missing_key_summary$missing_year == 0
)

# 3.2 Every geo maps to exactly one country_name
geo_to_country_check <- master_panel |>
  group_by(geo) |>
  summarise(
    country_name_count = n_distinct(country_name),
    country_names = paste(sort(unique(country_name)), collapse = " | "),
    .groups = "drop"
  ) |>
  filter(country_name_count != 1)
stopifnot(nrow(geo_to_country_check) == 0)

# 3.3 Every country_name maps to exactly one geo
country_to_geo_check <- master_panel |>
  group_by(country_name) |>
  summarise(
    geo_count = n_distinct(geo),
    geo_codes = paste(sort(unique(geo)), collapse = " | "),
    .groups = "drop"
  ) |>
  filter(geo_count != 1)
stopifnot(nrow(country_to_geo_check) == 0)

# 3.4 Geographic code format: two uppercase letters
geo_format_check <- master_panel |>
  distinct(geo) |>
  mutate(
    character_count = nchar(geo),
    valid_format = str_detect(geo, "^[A-Z]{2}$")
  ) |>
  filter(!valid_format)
stopifnot(nrow(geo_format_check) == 0)

# 3.5 No missing or blank country names
missing_country_name <- master_panel |>
  filter(is.na(country_name) | str_trim(country_name) == "")
stopifnot(nrow(missing_country_name) == 0)

# 3.6 Cohort flags is_eu27 and is_big6 remain stable within each economy
flag_stability_check <- master_panel |>
  group_by(geo, country_name) |>
  summarise(
    eu27_values = n_distinct(is_eu27),
    big6_values = n_distinct(is_big6),
    .groups = "drop"
  ) |>
  filter(eu27_values != 1 | big6_values != 1)
stopifnot(nrow(flag_stability_check) == 0)

# ============================================================
# Step 4 - Classify all 47 columns by analytical role
# ============================================================

key_columns <- c("geo", "year")

descriptive_dimensions <- c("country_name")

cohort_dimensions <- c("is_eu27", "is_big6", "in_density_sample")

derived_measures <- c(
  "gas_fc_twh",
  "retailers_per_twh",
  "retailers_per_million",
  "unable_warm_income_gap_pp",
  "utility_arrears_income_gap_pp",
  "e_cap_other_major_share",
  "e_gen_other_major_share",
  "e_cap_gross_churn_mw"
)

column_inventory <- tibble(column_name = names(master_panel)) |>
  mutate(
    column_position = match(column_name, names(master_panel)),
    r_type = vapply(
      master_panel[column_name],
      function(x) class(x)[1],
      character(1)
    ),
    analytical_role = case_when(
      column_name %in% key_columns ~ "Key",
      column_name %in% descriptive_dimensions ~ "Descriptive dimension",
      column_name %in% cohort_dimensions ~ "Cohort/eligibility dimension",
      column_name %in% derived_measures ~ "Derived measure",
      TRUE ~ "Base/input measure"
    )
  ) |>
  select(column_position, column_name, r_type, analytical_role) |>
  arrange(column_position)

print(column_inventory, n = Inf)

role_summary <- column_inventory |>
  count(analytical_role, name = "column_count") |>
  arrange(desc(column_count))
print(role_summary)

classification_check <- column_inventory |>
  summarise(
    source_column_count = ncol(master_panel),
    classified_column_count = n(),
    unique_classified_columns = n_distinct(column_name),
    unclassified_columns = sum(is.na(analytical_role)),
    duplicated_classifications = classified_column_count - unique_classified_columns
  )
print(classification_check)
stopifnot(
  classification_check$source_column_count == 47,
  classification_check$unclassified_columns == 0,
  classification_check$duplicated_classifications == 0
)

# ============================================================
# Step 5 - Targeted profiling for MySQL datatype design
# Purpose: collect only schema-relevant bounds, nulls, integer & sign status
# ============================================================

numeric_columns <- master_panel |>
  select(where(is.numeric)) |>
  names()

datatype_profile <- map_dfr(
  numeric_columns,
  function(col) {
    x <- master_panel[[col]]
    observed <- x[!is.na(x)]
    tibble(
      column_name = col,
      missing_count = sum(is.na(x)),
      minimum = if (length(observed) > 0) min(observed) else NA_real_,
      maximum = if (length(observed) > 0) max(observed) else NA_real_,
      whole_number_only = if (length(observed) > 0) {
        all(abs(observed - round(observed)) < 1e-9)
      } else {
        NA
      },
      contains_negative = if (length(observed) > 0) {
        any(observed < 0)
      } else {
        NA
      }
    )
  }
)

print(datatype_profile, n = Inf)
cat("\nAll R profiling and grain-validation checks passed.\n")
