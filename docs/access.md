# Who sees what

Two controls keep customer data where it belongs. Both are generated or tested, so they
cannot drift quietly.

## Personal data is masked before it reaches a BI tool

`marts.dim_customer` holds the real customer name. Dashboards never read it. They read
`reporting.rpt_customers`, a view with the same grain and key in which:

| Source | In the reporting view |
|---|---|
| `customer_name` | `customer_label`, a stable pseudonym such as `Customer BCFA3CCA` derived from a hash of the customer id |
| `contact_email` | `email_domain`, the part after the `@` |
| `customer_id` | not exposed |
| `region`, tier and dates | unchanged |

Two dbt tests guard it: one fails if any row still shows a name, a full email address
or an id; the other fails if two customers ever share a label. The generated LookML has
a test that no view or explore refers to `dim_customer` or `customer_name`.

For this to hold on BigQuery, the Looker service account should be granted the reporting
dataset only, with the view authorized over the marts. That grant is deployment
configuration; nothing in this repository sets it up and no deployment exists yet.

## Rows are limited by region

The LookML model uses two Looker user attributes:

| Attribute | Set to | Effect |
|---|---|---|
| `support_region` | a region (`EMEA`), a list (`NA, LATAM`) or `%` | The **Cases** explore is filtered to customers in those regions (`access_filter` on `customers.region`) |
| `support_scope` | `global` | Opens the **Support metrics (daily)** and **Backlog** explores |

The two aggregate explores have no customer on their rows, so they cannot be filtered by
region. Instead of showing a regional lead global numbers, they are closed to everyone
without the global scope. A regional lead gets the same metrics from the Cases explore,
filtered to their region.

## What has and has not been verified

- The masking tests run in CI on every build (DuckDB).
- The LookML parses, and tests check the access rules are present on every explore.
- The model has not been loaded into a Looker instance: there is no Looker licence
  behind this project. The access rules follow Looker's documented behaviour for
  `access_filter` and `access_grant` but have not been exercised by a real user session.
