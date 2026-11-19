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

---

## 8. Implied vs. Realized Volatility & Volatility Risk Premium

### 8.1 Trailing Realized Volatility
Measures historical realized volatility over the past $W = 21$ trading days ending at date $t$:
$$\sigma_{\text{trailing\_21d}, t} = \sqrt{\frac{1}{W - 1} \sum_{k=0}^{W-1} (r_{t-k} - \bar{r})^2} \times \sqrt{252}$$
Strictly backward-looking; available at date $t$.

### 8.2 Forward Realized Volatility (Retrospective Evaluation)
Measures the actual realized volatility that manifested over the subsequent $W = 21$ trading days:
$$\sigma_{\text{forward\_21d\_retrospective}, t} = \sqrt{\frac{1}{W - 1} \sum_{k=1}^{W} (r_{t+k} - \bar{r}_{\text{fwd}})^2} \times \sqrt{252}$$
**Methodological Constraint**: This metric uses future returns $[t+1, \dots, t+21]$ and serves exclusively as a retrospective benchmark to evaluate option pricing efficiency. It is never a trade signal.

### 8.3 Volatility Risk Premium (VRP) Spread
$$\text{VRP}_t = \text{VIX}_t - \sigma_{\text{forward\_21d\_retrospective}, t}$$
- $\text{VRP}_t > 0$: Implied volatility exceeded subsequent realized volatility (positive variance risk premium earned by option sellers).
- $\text{VRP}_t < 0$: Market experienced a volatility shock exceeding implied expectations.

---

## 9. European Option Pricing, Greeks, & Limits for Index Options

### 9.1 Black-Scholes-Merton Formulation
Under the assumptions of Geometric Brownian Motion, frictionless markets, and constant parameters, European call ($C$) and put ($P$) prices are:
$$C = S \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S \cdot N(-d_1)$$
where:
$$d_1 = \frac{\ln(S / K) + \left(r + \frac{1}{2}\sigma^2\right)T}{\sigma \sqrt{T}}, \quad d_2 = d_1 - \sigma \sqrt{T}$$
$N(x)$ is the cumulative standard normal distribution function:
$$N(x) = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{x} e^{-\frac{u^2}{2}} \, du = \frac{1}{2} \left[ 1 + \text{erf}\left( \frac{x}{\sqrt{2}} \right) \right]$$

### 9.2 The Analytical Greeks
The sensitivities of the option price with respect to market parameters are:
- **Delta ($\Delta$)**: Rate of change wrt underlying spot price $S$:
  $$\Delta_{\text{call}} = N(d_1) \in [0, 1], \quad \Delta_{\text{put}} = N(d_1) - 1 = -N(-d_1) \in [-1, 0]$$
- **Gamma ($\Gamma$)**: Curvature / rate of change of Delta wrt $S$:
  $$\Gamma = \frac{n(d_1)}{S \sigma \sqrt{T}} \ge 0 \quad (\text{identical for Call and Put})$$
- **Vega ($\mathcal{V}$)**: Sensitivity wrt volatility $\sigma$:
  $$\mathcal{V} = S \sqrt{T} n(d_1) \ge 0 \quad (\text{identical for Call and Put})$$
- **Theta ($\Theta$)**: Time decay rate (annualized $-\frac{\partial V}{\partial T}$):
  $$\Theta_{\text{call}} = -\frac{S n(d_1) \sigma}{2\sqrt{T}} - r K e^{-rT} N(d_2)$$
  $$\Theta_{\text{put}} = -\frac{S n(d_1) \sigma}{2\sqrt{T}} + r K e^{-rT} N(-d_2)$$
- **Rho ($\rho$)**: Sensitivity wrt risk-free interest rate $r$:
  $$\rho_{\text{call}} = K T e^{-rT} N(d_2), \quad \rho_{\text{put}} = -K T e^{-rT} N(-d_2)$$

### 9.3 Put-Call Parity
By absence of static arbitrage:
$$C - P = S - K \cdot e^{-rT}$$
holds exactly for all European options on non-dividend-paying assets regardless of volatility dynamics.

### 9.4 Implied Volatility Inversion
Given an observed market price $V_{\text{mkt}}$, implied volatility $\sigma_{\text{imp}}$ is the unique root solving:
$$f(\sigma) = \text{BS}(S, K, r, \sigma, T) - V_{\text{mkt}} = 0$$
Solved via Newton-Raphson iteration:
$$\sigma_{n+1} = \sigma_n - \frac{\text{BS}(S, K, r, \sigma_n, T) - V_{\text{mkt}}}{\mathcal{V}(S, K, r, \sigma_n, T)}$$
with robust bisection fallback when Vega is small or iterations drift outside $[10^{-4}, 5.0]$.

### 9.5 Methodological Limitations of Black-Scholes for Index Options (NIFTY 50)
While Black-Scholes provides a baseline analytical framework, index options in practice (such as NIFTY 50 European weekly and monthly contracts traded on the NSE) systematically violate core model assumptions:

1. **Volatility Skew and Smile (Non-Constant Volatility)**:
   - *Assumption*: Volatility $\sigma$ is constant across all strike prices $K$ and maturities $T$.
   - *Reality*: Nifty 50 options display a pronounced **downward volatility skew** (the "volatility smirk"). Out-of-the-money (OTM) puts trade at substantially higher implied volatilities than ATM or OTM calls. This arises from institutional hedging demand (downside portfolio insurance) and structural leverage effects.

2. **Fat Tails and Jump-Diffusion (Non-Log-Normal Returns)**:
   - *Assumption*: Underlying asset prices follow a continuous Geometric Brownian Motion with log-normal returns.
   - *Reality*: Empirical index returns exhibit **excess kurtosis (fat tails)** and **negative skewness**. Sudden market gapping—driven by weekend events, central bank policy announcements, geopolitical shocks, or election outcomes—cannot be generated by pure Brownian diffusion, causing BSM to severely underprice deep OTM tail options.

3. **Discrete Index Dividends**:
   - *Assumption*: Underlying index pays no dividends or a constant continuous dividend yield $q$.
   - *Reality*: The 50 constituent stocks of the NIFTY 50 pay discrete, seasonal dividends (typically clustering between May and August). Omitting index dividend yields overstates call options and understates put options, especially for quarterly and semi-annual expiries.

4. **Stochastic Volatility and Clustering**:
   - *Assumption*: Future volatility is deterministic and unchanging.
   - *Reality*: Volatility clusters into high-volatility regimes and low-volatility regimes (ARCH/GARCH effects), and volatility is negatively correlated with index returns (leverage effect). Models like Heston (1993) or SABR are required to capture volatility dynamics accurately.

5. **Market Microstructure and Settlement Friction**:
   - *Assumption*: Frictionless continuous trading, zero bid-ask spread, zero transaction costs.
   - *Reality*: In Indian derivative markets, Securities Transaction Tax (STT), exchange turnover charges, bid-ask spreads in illiquid OTM wings, and discrete trading sessions restrict continuous dynamic delta hedging.

---

## 10. Event Study Methodology: Union Budget Impact Analysis

### 10.1 Event Definition & Calendar Mapping
The event is the presentation of the Government of India Union Budget to Parliament:
- **Event Day $\tau = 0$**: Defined as the official Budget presentation date. If the presentation occurs on a weekend or exchange holiday when Indian markets are closed (e.g. Saturday, 2020-02-01), $\tau = 0$ is assigned to the immediate next regular NSE trading session (Monday, 2020-02-03) and documented explicitly.
- **Master Trading Calendar**: All relative event days $\tau$ are indexed strictly in **trading days** (exchange trading sessions) rather than calendar days.

### 10.2 Timeline Specification
For each event $i$:
1. **Estimation Window**: $\tau \in [-120, -21]$ (100 trading days). This window ends 21 trading days prior to the budget to ensure parameter estimates are unpolluted by pre-budget leaks, rumors, or positioning.
2. **Event Window**: $\tau \in [-5, +5]$ (11 trading days centered on presentation day $\tau = 0$).

### 10.3 Normal and Abnormal Return Modeling
For asset return $R_{i, \tau}$ on relative event day $\tau$:

#### 1. NIFTY 50 (Constant Mean Return Model)
The normal benchmark return $\bar{R}_i$ is the sample mean daily log return during the estimation window:
$$\bar{R}_i = \frac{1}{100} \sum_{\tau=-120}^{-21} R_{\text{NIFTY}, i, \tau}$$
The abnormal return on event day $\tau \in [-5, +5]$ is:
$$AR_{\text{NIFTY}, i, \tau} = R_{\text{NIFTY}, i, \tau} - \bar{R}_i$$

#### 2. Bank NIFTY (Market Model Regression)
Because Bank NIFTY is strongly correlated with the broader market but carries sector-specific beta exposure, normal return is estimated via an Ordinary Least Squares (OLS) regression against NIFTY 50 over the estimation window $[-120, -21]$:
$$R_{\text{BN}, i, \tau} = \hat{\alpha}_i + \hat{\beta}_i R_{\text{NIFTY}, i, \tau} + \epsilon_{i, \tau}$$
where:
$$\hat{\beta}_i = \frac{\text{Cov}(R_{\text{BN}}, R_{\text{NIFTY}})}{\text{Var}(R_{\text{NIFTY}})}, \quad \hat{\alpha}_i = \bar{R}_{\text{BN}, i} - \hat{\beta}_i \bar{R}_{\text{NIFTY}, i}$$
The abnormal return in the event window is:
$$AR_{\text{BN}, i, \tau} = R_{\text{BN}, i, \tau} - \left( \hat{\alpha}_i + \hat{\beta}_i R_{\text{NIFTY}, i, \tau} \right)$$

### 10.4 Cumulative Abnormal Returns (CAR)
Cumulative abnormal returns aggregate abnormal performance across multi-day sub-windows:
$$CAR_i[\tau_1, \tau_2] = \sum_{\tau=\tau_1}^{\tau_2} AR_{i, \tau}$$
The study computes:
- **Announcement Window $CAR[-1, +1]$**: Captures the immediate 3-day market reaction including day -1 pre-positioning and day +1 digestion.
- **Post-Budget Drift Window $CAR[0, +5]$**: Captures post-presentation policy absorption over the subsequent week.

### 10.5 Level Changes for India VIX and USD/INR
For non-stationary economic series (implied volatility and currency levels), measuring percentage returns can obscure regime shifts. The study tracks the **cumulative change in level relative to pre-event baseline (Day -1)**:
$$\Delta \text{VIX}_{i, \tau} = \text{VIX}_{i, \tau} - \text{VIX}_{i, -1} \quad (\text{percentage points})$$
$$\Delta \text{USDINR}_{i, \tau} = \text{USDINR}_{i, \tau} - \text{USDINR}_{i, -1} \quad (\text{rupees per dollar})$$

### 10.6 Cross-Sectional Aggregation & Significance Testing
Across the $N = 9$ Budget events:
- **Average Abnormal Return (AAR)**:
  $$AAR_{\tau} = \frac{1}{N} \sum_{i=1}^N AR_{i, \tau}$$
- **Cumulative Average Abnormal Return (CAAR)**:
  $$CAAR[\tau_1, \tau_2] = \frac{1}{N} \sum_{i=1}^N CAR_i[\tau_1, \tau_2]$$
- **Standard Error & Cross-Sectional $t$-statistic**:
  $$s = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N \left( CAR_i[\tau_1, \tau_2] - CAAR[\tau_1, \tau_2] \right)^2}$$
  $$SE(CAAR) = \frac{s}{\sqrt{N}}, \quad t_{\text{stat}} = \frac{CAAR[\tau_1, \tau_2]}{SE(CAAR)}$$
Under the null hypothesis $H_0: CAAR = 0$, $t_{\text{stat}}$ follows a Student's $t$-distribution with $N - 1$ degrees of freedom. Statistical significance is rejected unless $p\text{-value} < 0.05$.



