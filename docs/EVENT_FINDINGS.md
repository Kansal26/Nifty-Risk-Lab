# Union Budget Event Study: Findings & Empirical Analysis (2019–2026)

This report details the empirical findings from an event study evaluating the market impact of the **9 most recent Government of India Union Budget presentations** (July 2019 to February 2026) on the **NIFTY 50**, **Bank NIFTY**, **India VIX**, and **USD/INR**. All 9 presentations were delivered by Union Finance Minister Nirmala Sitharaman.

---

## 1. Executive Summary

| Metric | Sample Mean | Standard Error ($SE$) | $t$-statistic | $p$-value ($t$-test) | Statistically Significant at 5%? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **NIFTY 50 Day-0 Abnormal Return** | $+0.042\%$ | $0.634\%$ | $+0.066$ | $0.9490$ | **No** (Fail to reject $H_0$) |
| **NIFTY 50 $CAR[-1, +1]$** | $+0.710\%$ | $0.842\%$ | $+0.842$ | $0.4240$ | **No** (Fail to reject $H_0$) |
| **NIFTY 50 $CAR[0, +5]$** | $+0.817\%$ | $1.158\%$ | $+0.705$ | $0.5006$ | **No** (Fail to reject $H_0$) |
| **Bank NIFTY Day-0 Abnormal Return** | $+0.162\%$ | $0.241\%$ | $+0.673$ | $0.5197$ | **No** (Fail to reject $H_0$) |
| **Bank NIFTY $CAR[-1, +1]$** | $+0.284\%$ | $0.455\%$ | $+0.625$ | $0.5492$ | **No** (Fail to reject $H_0$) |
| **Bank NIFTY $CAR[0, +5]$** | $-0.208\%$ | $0.483\%$ | $-0.431$ | $0.6777$ | **No** (Fail to reject $H_0$) |
| **India VIX Day-0 Level Change** | **$-1.131$ pts** | **$0.354$ pts** | **$-3.196$** | **$0.0127$** | **Yes** ($p < 0.05$, Reject $H_0$) |
| **USD/INR Day-0 Level Change** | $-0.105$ INR | $0.062$ INR | $-1.695$ | $0.1285$ | **No** (Fail to reject $H_0$) |

### Key Conclusions:
1. **No Statistically Significant Abnormal Equity Return**: Across the 9 recent budget presentations, neither NIFTY 50 nor Bank NIFTY exhibited statistically significant abnormal returns on Day 0 or over the multi-day announcement windows ($CAR[-1, +1]$ and $CAR[0, +5]$). The sample mean CAR[-1, +1] is $+0.710\%$ for NIFTY 50 ($p = 0.4240$) and $+0.284\%$ for Bank NIFTY ($p = 0.5492$), failing to reject the null hypothesis of market efficiency.
2. **Day-0 Win Rate of 22.2%**: Only 2 out of the 9 presentations recorded positive Day-0 abnormal returns for NIFTY 50 (February 1, 2021 at $+4.41\%$ and February 1, 2022 at $+1.29\%$), while 7 events registered negative Day-0 abnormal returns.
3. **Statistically Significant Implied Volatility Crush**: As observed across longer horizons, the single statistically robust phenomenon is the **Day-0 compression in India VIX** ($\text{mean} = -1.131\text{ points}, t = -3.196, p = 0.0127$). Implied volatility contracted on 7 of 9 presentations (unchanged on 2025-02-01, slight uptick on 2026-02-01), confirming systematic resolution of event uncertainty.
4. **Muted Currency Response**: USD/INR appreciated by an average of $-0.105$ INR per USD on presentation day, but this shift is not statistically significant ($p = 0.1285$).

---

## 2. Event-by-Event Results Table

*Source: `data/clean/budget_event_study.parquet` & `market_daily.parquet`*

| Event Date | Effective Trading Day 0 | Presentation Day Market Open? | Budget Type | NIFTY Day 0 AR (%) | NIFTY $CAR[-1,+1]$ (%) | NIFTY $CAR[0,+5]$ (%) | Bank NIFTY Day 0 AR (%) | Bank NIFTY $CAR[-1,+1]$ (%) | Bank NIFTY $CAR[0,+5]$ (%) | India VIX Day 0 $\Delta$ (pts) | USD/INR Day 0 $\Delta$ (₹) | Key Policy / Macro Context |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2019-07-05** | 2019-07-05 | Yes | Regular | $-1.24\%$ | $-3.35\%$ | $-3.95\%$ | $+1.29\%$ | $+0.89\%$ | $+0.90\%$ | $-0.46$ | $-0.27$ | Maiden budget of FM Nirmala Sitharaman; surcharge on high earners and FPIs. |
| **2020-02-01** | 2020-02-03 | **No** (Sat $\to$ Mon) | Regular | $-2.25\%$ | $-0.79\%$ | $-0.06\%$ | $+0.47\%$ | $+0.88\%$ | $+0.04$ | $-1.59$ | $-0.14$ | Saturday presentation; exchange closed, Day 0 rolled to Monday Feb 3 (2020-02-03). |
| **2021-02-01** | 2021-02-01 | Yes | Regular | $+4.41\%$ | $+5.17\%$ | $+8.99\%$ | $+0.85\%$ | $+3.14\%$ | $+0.44\%$ | $-2.02$ | $-0.03$ | First paperless post-COVID recovery budget with infrastructure capex. |
| **2022-02-01** | 2022-02-01 | Yes | Regular | $+1.29\%$ | $+3.69\%$ | $-0.82\%$ | $+0.01\%$ | $+0.32\%$ | $+1.08\%$ | $-1.97$ | $-0.48$ | Gati Shakti capex focus and taxation framework for virtual digital assets. |
| **2023-02-01** | 2023-02-01 | Yes | Regular | $-0.30\%$ | $-0.35\%$ | $+0.91\%$ | $-0.14\%$ | $+0.69\%$ | $+0.36\%$ | $-0.10$ | $+0.19$ | Rebate threshold increase under new income tax regime. |
| **2024-02-01** | 2024-02-01 | Yes | Interim | $-0.25\%$ | $+1.18\%$ | $-0.73\%$ | $+0.60\%$ | $-0.20\%$ | $-1.87\%$ | $-1.59$ | $-0.06$ | Interim Budget ahead of 2024 General Elections; fiscal deficit consolidation. |
| **2024-07-23** | 2024-07-23 | Yes | Regular | $-0.21\%$ | $-0.73\%$ | $+0.91\%$ | $-0.86\%$ | $-1.38\%$ | $-3.26\%$ | $-2.69$ | $-0.06$ | Post-election full Union Budget; revised capital gains tax structure and STT hike. |
| **2025-02-01** | 2025-02-01 | **Yes** (Special) | Regular | $-0.10\%$ | $+0.52\%$ | $+0.31\%$ | $+0.09\%$ | $-0.76\%$ | $+0.78\%$ | $0.00$ | $0.00$ | Saturday presentation; special live NSE trading session held on Saturday Feb 1 (2025-02-01). |
| **2026-02-01** | 2026-02-02 | **No** (Sun $\to$ Mon) | Regular | $-0.98\%$ | $+1.03\%$ | $+1.79\%$ | $-0.84\%$ | $-1.04\%$ | $-0.34\%$ | $+0.24$ | $-0.09$ | Sunday presentation; exchange closed, Day 0 rolled to Monday Feb 2 (2026-02-02). |
| **Average** | — | — | — | **$+0.04\%$** | **$+0.71\%$** | **$+0.82\%$** | **$+0.16\%$** | **$+0.28\%$** | **$-0.21\%$** | **$-1.13$** | **$-0.11$** | **Cross-Event Mean** |
| **Std Error** | — | — | — | **$0.63\%$** | **$0.84\%$** | **$1.16\%$** | **$0.24\%$** | **$0.45\%$** | **$0.48\%$** | **$0.35$** | **$0.06$** | **Standard Error ($s / \sqrt{N}$)** |

---

## 3. Visual Trajectory Analysis

![Union Budget Cumulative Abnormal Return Paths](figures/budget_event_study_car.png)

The chart above displays the cumulative abnormal return trajectories across the $[-5, +5]$ event window:
- **Individual event paths** (light gray lines) illustrate large dispersion across different budget years. In 2021 (post-COVID capex budget), NIFTY 50 experienced a dramatic $+8.99\%$ CAR drift over $[0, +5]$, whereas in 2019 (super-rich surcharge and FPI tax friction), NIFTY suffered a $-3.95\%$ post-budget downward drift.
- **Cross-event average CAAR** (bold blue line for NIFTY 50, bold orange line for Bank NIFTY) remains largely flat across the window, rising modestly to $+0.71\%$ on Day +1 and leveling off without statistical persistence.

---

## 4. Methodological Limitations

When interpreting these results, several critical limitations must be explicitly considered:

### 1. Small Sample Size ($N = 9$)
With only 9 budget events between 2019 and 2026, the cross-sectional statistical power of Student's $t$-tests is inherently constrained. A sample of 9 observations requires a $t$-statistic of $|t| \ge 2.306$ to reach the conventional $5\%$ significance threshold ($df = 8$). The findings should be treated as **indicative historical observations, not definitive statistical laws**.

### 2. Overlapping Macro Confounders
No national budget takes place in a vacuum:
- **2020 Budget**: Presented just as initial reports of the COVID-19 outbreak in Wuhan emerged globally, culminating in the March 2020 global liquidity shock.
- **Global Monetary Cycles**: The 2022–2023 budgets coincided with US Federal Reserve monetary tightening cycles and foreign institutional investor (FII) capital reallocation.
- **Geopolitical Shocks**: Pre-budget and post-budget windows frequently coincide with global crude oil price swings and geopolitical tension.

### 3. Structural Heterogeneity: Interim vs. Full Budgets
The sample pools **8 Full Budgets** and **1 Interim Budget** (February 2024):
- Interim budgets are constitutional "votes on account" intended to fund government operations until elections conclude; by convention, major structural taxation overhauls are avoided.
- Full budgets carry far higher policy scope.

### 4. Presentation During Active Market Hours
Unlike US corporate earnings releases (which occur pre-market or after-hours), the Union Budget speech begins at **11:00 AM IST on the presentation day**:
- The announcement unfolds sequentially over 90 to 120 minutes during live exchange trading.
- Markets frequently experience severe intraday swings (spiking on corporate tax cuts, crashing on capital gains tax increases, whipsawing on sector capex allocations) before settling by 3:30 PM IST.
- Daily close-to-close returns compress these large intraday volatility spikes into a single net move, understating the actual execution risk faced by intraday market participants.
