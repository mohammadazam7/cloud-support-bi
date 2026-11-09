# Metric dictionary

Every support metric, its owner and exactly how it is computed. This page is
written by `support-bi metrics` from `metrics/metrics.yml`; edit the YAML, not
this file.

| Metric | Definition | Computed as | Unit | Better | Owner |
| --- | --- | --- | --- | --- | --- |
| **Cases opened** (`case_volume`) | Number of cases opened in the period. | sum(cases) over agg_support_daily | cases | neutral | Support Operations |
| **First-response SLA attainment** (`first_response_sla_attainment`) | Share of cases whose first agent response came within the target for the case's priority and the support tier the customer held when the case was opened. | sum(first_response_sla_met_cases) / sum(cases) over agg_support_daily | share | higher | Support Operations |
| **Mean first-response time** (`mean_first_response_minutes`) | Average minutes from case creation to the first agent response. | sum(first_response_minutes_sum) / sum(cases) over agg_support_daily | minutes | lower | Support Operations |
| **Median first-response time** (`median_first_response_minutes`) | Median minutes to first response. Reported with the mean because a few very slow responses move the mean a long way. | 0.5 quantile of first_response_minutes in fct_cases | minutes | lower | Support Operations |
| **Mean time to resolve** (`mean_resolution_hours`) | Average hours from case creation to the first resolution. | sum(resolution_hours_sum) / sum(cases) over agg_support_daily | hours | lower | Support Operations |
| **Escalation rate** (`escalation_rate`) | Share of cases escalated to engineering at least once. | sum(escalated_cases) / sum(cases) over agg_support_daily | share | lower | Support Engineering |
| **Reopen rate** (`reopen_rate`) | Share of resolved cases the customer reopened. | sum(reopened_cases) / sum(cases) over agg_support_daily | share | lower | Support Quality |
| **CSAT (mean score)** (`csat_score`) | Mean satisfaction score over survey responses; cases without a response are excluded. | sum(csat_score_sum) / sum(csat_responses) over agg_support_daily | score 1 to 5 | higher | Support Quality |
| **CSAT (share satisfied)** (`csat_satisfied_share`) | Share of survey responses scoring 4 or 5. | sum(csat_satisfied_responses) / sum(csat_responses) over agg_support_daily | share | higher | Support Quality |
| **Survey response rate** (`csat_response_rate`) | Share of cases with a satisfaction survey response. Read CSAT alongside it. | sum(csat_responses) / sum(cases) over agg_support_daily | share | higher | Support Quality |
| **Open backlog** (`open_backlog`) | Cases open at the end of the day, averaged over the days in the period. | mean over days of daily sum(open_cases) in fct_backlog_daily | cases | lower | Support Operations |

Every metric can be grouped and filtered by `date`, `month`, `product_code`, `priority`, `tier`, `channel`, except that
`tier` and `channel` do not apply to the backlog.
