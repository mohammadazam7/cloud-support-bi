# Architecture decision records

Each record states a decision, the context it was made in, and its consequences, in the
format described by Michael Nygard. Records are not edited after they are accepted; a
later record supersedes an earlier one.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-type-2-customer-tier.md) | Keep customer tier history as a type 2 dimension | Accepted |
| [0002](0002-utc-at-the-staging-boundary.md) | Convert timestamps to UTC explicitly in staging | Accepted |
| [0003](0003-additive-metric-components.md) | Store additive metric components, not ratios | Accepted |
| [0004](0004-raw-zone-as-dbt-sources.md) | Declare the raw zone as dbt sources on both targets | Accepted |
