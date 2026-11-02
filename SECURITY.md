# Security policy

## Reporting a problem

Please report security issues privately through GitHub's
[security advisories](https://github.com/mohammadazam7/cloud-support-bi/security/advisories/new)
rather than in a public issue. Expect an acknowledgement within a few days.

## Data and credentials

- All data in this repository is synthetic. No real customer, agent or case data is
  stored or processed.
- Credentials (for example a BigQuery service account key) are read from the
  environment and are never committed. `.gitignore` excludes common key file names.
- Columns that would identify a person in a real deployment (customer name, contact
  email) are masked in the reporting layer and covered by row-level access rules.
