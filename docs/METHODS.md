# Mathematical Methods and Formulas

This document details all mathematical formulas, econometric definitions, conventions, and assumptions used throughout `nifty-risk-lab`.

---

## 1. Return Calculations

### 1.1 Daily Simple Return
The simple percentage return $R_t$ between day $t-1$ and day $t$ is defined as:
$$R_t = \frac{P_t - P_{t-1}}{P_{t-1}} = \frac{P_t}{P_{t-1}} - 1$$
where $P_t$ is the adjusted closing price at date $t$.

### 1.2 Daily Log (Continuously Compounded) Return
The project standardizes on **log returns** ($r_t$):
$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(P_t) - \ln(P_{t-1})$$

#### Why Log Returns?
1. **Time Additivity**: Multi-period compounding is additive:
   $$r_{0, T} = \sum_{t=1}^{T} r_t = \ln(P_T) - \ln(P_0)$$
2. **Symmetry**: Percentage gains and losses are asymmetric (a $+50\%$ gain followed by a $-50\%$ loss leaves an investor at $0.75 \times P_0$), whereas equal and opposite log returns sum to zero ($\ln(1.5) + \ln(1/1.5) = 0$).
3. **Statistical Tractability**: Log price differences are standard assumptions in continuous-time financial modeling and Brownian motion representations.

---

## 2. Volatility and Annualisation

### 2.1 Daily Realized Volatility (Sample Standard Deviation)
For a sample of $N$ daily log returns with mean $\bar{r}$:
$$\sigma_{\text{daily}} = \sqrt{\frac{1}{N - 1} \sum_{t=1}^{N} (r_t - \bar{r})^2}$$

### 2.2 Annualisation Factor ($\sqrt{252}$)
Under the assumption of independently and identically distributed (i.i.d.) returns across trading days, variance scales linearly with time:
$$\text{Var}_{\text{ann}} = 252 \times \text{Var}_{\text{daily}}$$
Therefore, annualised volatility is:
$$\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{252}$$
*Assumption*: The Indian equity market (NSE) observes approximately **252 trading days** per calendar year (excluding weekends and exchange holidays).

---

## 3. Implied Volatility (India VIX)

### 3.1 Definition of India VIX
India VIX measures the expected market volatility over the next 30 calendar days, annualized as a percentage, derived from the bid-ask quotes of near and next-month NIFTY index options contracts (based on the Black-Scholes / CBOE VIX computation methodology).

### 3.2 Daily Implied Volatility Conversion
To express the annualized VIX as a daily equivalent volatility:
$$\sigma_{\text{daily, implied}} = \frac{\text{VIX}_t}{100 \times \sqrt{252}}$$

---

## 4. Look-Ahead Bias Prevention Standards

1. **Information Filtration $\mathcal{F}_t$**: Any indicator, calculation, signal, or feature calculated for date $t$ must strictly use data $\le t$.
2. **Point-in-Time Index Alignment**: When merging index data and volatility index data, joins are strictly performed on matching trading calendar dates $t$. Missing historical dates are never forward-filled from future dates ($t+k$).
3. **Retrospective Labeling**: Any forward-looking computation (e.g., forward realized volatility over $[t+1, t+30]$ used to evaluate VIX forecast accuracy) must be explicitly flagged with `_retrospective` or `_ex_post` in column headers and variable names.

---

## 5. Drawdown Analytics

### 5.1 Running Maximum Price & Underwater Drawdown
For a price series $P_t$, the running peak price up to date $t$ is:
$$M_t = \max_{s \le t} P_s$$

The percentage drawdown $DD_t$ measures the loss relative to the prior high water mark:
$$DD_t = \frac{P_t - M_t}{M_t} = \frac{P_t}{M_t} - 1 \le 0$$

The running maximum drawdown up to date $t$ is:
$$MDD_t = \min_{s \le t} DD_s$$

### 5.2 Discrete Drawdown Episode Identification
A discrete drawdown cycle begins at peak date $t_{\text{peak}}$, reaches trough date $t_{\text{trough}}$ where $P_{\text{trough}} = \min_{t_{\text{peak}} \le s \le t_{\text{rec}}} P_s$, and concludes on recovery date $t_{\text{rec}}$ when $P_{t_{\text{rec}}} \ge P_{\text{peak}}$.

---

## 6. Value at Risk (VaR) Modeling

Value at Risk ($\text{VaR}_\alpha$) at confidence level $(1 - \alpha)$ over a 1-day horizon specifies the maximum loss expected over 1 day such that:
$$P(r_t < \text{VaR}_{\alpha, t}) \le \alpha$$

### 6.1 Look-Ahead Prevention Convention
To ensure zero look-ahead bias, the VaR threshold for trading date $t$ is estimated using a rolling historical lookback window of $W = 250$ trading days terminating on date $t-1$:
$$\text{Window}_t = [r_{t-250}, r_{t-249}, \dots, r_{t-1}]$$

### 6.2 Historical Simulation VaR
Historical simulation makes no parametric distributional assumption and estimates VaR directly as the empirical $\alpha$-quantile of the lagged 250-day return distribution:
$$\text{VaR}_{\text{hist}, \alpha, t} = \text{Quantile}\left(\text{Window}_t, \alpha\right)$$
For $\alpha = 0.05$ (95% confidence), it selects the 5th percentile; for $\alpha = 0.01$ (99% confidence), the 1st percentile.

### 6.3 Parametric Normal (Gaussian) VaR
Under the assumption that daily returns are normally distributed with sample mean $\mu_{t-1}$ and sample standard deviation $\sigma_{t-1}$:
$$\text{VaR}_{\text{norm}, \alpha, t} = \mu_{t-1} + z_\alpha \cdot \sigma_{t-1}$$
where $z_{0.05} \approx -1.64485$ and $z_{0.01} \approx -2.32635$.

---

## 7. VaR Backtesting & Kupiec POF Test

### 7.1 Exception (Breach) Indicator
An exception occurs on day $t$ if the realized daily log return is strictly worse than the 1-day ahead VaR forecast:
$$I_t = \mathbb{I}\left(r_t < \text{VaR}_{\alpha, t}\right)$$
Total observed breaches: $x = \sum_{t=1}^{N_{\text{eval}}} I_t$. Expected breaches: $E[x] = \alpha \times N_{\text{eval}}$.

### 7.2 Kupiec Proportion of Failures (POF) Likelihood Ratio Test
Tests the null hypothesis $H_0: p = \alpha$ against $H_1: p \neq \alpha$:
$$\text{LR}_{\text{POF}} = -2 \ln \left( \frac{(1 - \alpha)^{N - x} \alpha^x}{(1 - \hat{p})^{N - x} \hat{p}^x} \right) \sim \chi^2(1)$$
where $\hat{p} = x / N$. Under $H_0$, $\text{LR}_{\text{POF}}$ asymptotically follows a Chi-square distribution with 1 degree of freedom. If $p\text{-value} < 0.05$, the model's tail risk accuracy is rejected.
