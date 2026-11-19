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
