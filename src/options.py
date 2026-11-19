"""European option pricing, Greeks, and Implied Volatility engine for nifty-risk-lab.

Implemented from scratch using strictly standard Python math and numpy.
No external numerical optimization libraries used.

Models & Calculations:
1. Black-Scholes-Merton (1973) European call and put analytical pricing.
2. First and second-order Greeks: Delta, Gamma, Vega, Theta, and Rho.
3. Implied Volatility solver combining Newton-Raphson with Bisection fallback.

Assumptions:
- European-style exercise (exercisable only at maturity T).
- Frictionless markets (no transaction costs, continuous trading, borrow/lend at risk-free rate r).
- Constant risk-free interest rate r over the life of the option.
- Constant volatility sigma > 0.
- Underlying asset price follows a Geometric Brownian Motion with zero dividends (q = 0).
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

# Numerical tolerances
EPSILON = 1e-12
MAX_ITER = 100
VOL_TOL = 1e-8


def standard_normal_cdf(x: float) -> float:
    """Compute cumulative distribution function of standard normal N(0, 1).

    Formula:
        N(x) = 0.5 * (1 + erf(x / sqrt(2)))

    Parameters
    ----------
    x : float
        Input real number.

    Returns
    -------
    float
        Probability P(Z <= x) for Z ~ N(0, 1).
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def standard_normal_pdf(x: float) -> float:
    """Compute probability density function of standard normal N(0, 1).

    Formula:
        n(x) = (1 / sqrt(2 * pi)) * exp(-0.5 * x^2)

    Parameters
    ----------
    x : float
        Input real number.

    Returns
    -------
    float
        Density n(x).
    """
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def compute_d1_d2(
    spot: float, strike: float, rate: float, sigma: float, time_to_maturity: float
) -> tuple[float, float]:
    """Compute the d1 and d2 arguments in the Black-Scholes formula.

    Formulas:
        d1 = [ln(S / K) + (r + 0.5 * sigma^2) * T] / [sigma * sqrt(T)]
        d2 = d1 - sigma * sqrt(T)

    Parameters
    ----------
    spot : float
        Underlying spot price (S > 0).
    strike : float
        Strike price (K > 0).
    rate : float
        Risk-free annualized interest rate (e.g. 0.05 for 5%).
    sigma : float
        Annualized volatility (sigma > 0).
    time_to_maturity : float
        Time to maturity in years (T > 0).

    Returns
    -------
    tuple[float, float]
        (d1, d2)
    """
    if spot <= 0 or strike <= 0:
        raise ValueError("Spot and Strike prices must be strictly positive.")
    if sigma <= 0:
        raise ValueError("Volatility sigma must be strictly positive.")
    if time_to_maturity <= 0:
        raise ValueError("Time to maturity must be strictly positive.")

    sqrt_t = math.sqrt(time_to_maturity)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * time_to_maturity) / (
        sigma * sqrt_t
    )
    d2 = d1 - sigma * sqrt_t
    return d1, d2


def black_scholes_price(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Calculate Black-Scholes-Merton European option price.

    Formulas:
        Call: C = S * N(d1) - K * exp(-r * T) * N(d2)
        Put:  P = K * exp(-r * T) * N(-d2) - S * N(-d1)

    Parameters
    ----------
    spot : float
        Spot price of underlying asset (S > 0).
    strike : float
        Strike price (K > 0).
    rate : float
        Annualized risk-free interest rate (e.g. 0.10 for 10%).
    sigma : float
        Annualized volatility (e.g. 0.20 for 20%).
    time_to_maturity : float
        Time to maturity in years (e.g. 0.5 for 6 months).
    option_type : Literal['call', 'put']
        Option type ('call' or 'put').

    Returns
    -------
    float
        Theoretical European option price.
    """
    d1, d2 = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    discount = math.exp(-rate * time_to_maturity)

    opt = option_type.lower().strip()
    if opt == "call":
        return spot * standard_normal_cdf(d1) - strike * discount * standard_normal_cdf(d2)
    elif opt == "put":
        return strike * discount * standard_normal_cdf(-d2) - spot * standard_normal_cdf(-d1)
    else:
        raise ValueError(f"Invalid option_type: '{option_type}'. Must be 'call' or 'put'.")


def delta(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Calculate Delta: rate of change of option price with respect to underlying spot price.

    Formulas:
        Delta_call = N(d1)                  in [0, 1]
        Delta_put  = N(d1) - 1 = -N(-d1)    in [-1, 0]

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity, option_type
        Standard Black-Scholes inputs.

    Returns
    -------
    float
        Option Delta.
    """
    d1, _ = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    opt = option_type.lower().strip()
    if opt == "call":
        return standard_normal_cdf(d1)
    elif opt == "put":
        return standard_normal_cdf(d1) - 1.0
    else:
        raise ValueError(f"Invalid option_type: '{option_type}'")


def gamma(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
) -> float:
    """Calculate Gamma: second derivative of option price with respect to spot price.

    Formula:
        Gamma = n(d1) / [S * sigma * sqrt(T)] >= 0
    Identical for both European calls and puts.

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity
        Standard Black-Scholes inputs.

    Returns
    -------
    float
        Option Gamma (non-negative).
    """
    d1, _ = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    sqrt_t = math.sqrt(time_to_maturity)
    return standard_normal_pdf(d1) / (spot * sigma * sqrt_t)


def vega(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
) -> float:
    """Calculate Vega: rate of change of option price with respect to volatility sigma.

    Formula:
        Vega = S * sqrt(T) * n(d1) >= 0
    Identical for both European calls and puts.

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity
        Standard Black-Scholes inputs.

    Returns
    -------
    float
        Option Vega (non-negative).
    """
    d1, _ = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    return spot * math.sqrt(time_to_maturity) * standard_normal_pdf(d1)


def theta(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Calculate Theta: time decay rate (-dV / dT).

    Formulas:
        Theta_call = - [S * n(d1) * sigma] / [2 * sqrt(T)] - r * K * exp(-r * T) * N(d2)
        Theta_put  = - [S * n(d1) * sigma] / [2 * sqrt(T)] + r * K * exp(-r * T) * N(-d2)

    Note:
        Reported as annualized rate (-dV/dT). To obtain decay per calendar day, divide by 365.

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity, option_type
        Standard Black-Scholes inputs.

    Returns
    -------
    float
        Option Theta (annualized).
    """
    d1, d2 = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    sqrt_t = math.sqrt(time_to_maturity)
    discount = math.exp(-rate * time_to_maturity)

    term1 = -(spot * standard_normal_pdf(d1) * sigma) / (2.0 * sqrt_t)

    opt = option_type.lower().strip()
    if opt == "call":
        return term1 - rate * strike * discount * standard_normal_cdf(d2)
    elif opt == "put":
        return term1 + rate * strike * discount * standard_normal_cdf(-d2)
    else:
        raise ValueError(f"Invalid option_type: '{option_type}'")


def rho(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Calculate Rho: rate of change of option price with respect to risk-free rate r.

    Formulas:
        Rho_call = K * T * exp(-r * T) * N(d2)
        Rho_put  = - K * T * exp(-r * T) * N(-d2)

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity, option_type
        Standard Black-Scholes inputs.

    Returns
    -------
    float
        Option Rho.
    """
    _, d2 = compute_d1_d2(spot, strike, rate, sigma, time_to_maturity)
    discount = math.exp(-rate * time_to_maturity)
    t = time_to_maturity

    opt = option_type.lower().strip()
    if opt == "call":
        return strike * t * discount * standard_normal_cdf(d2)
    elif opt == "put":
        return -strike * t * discount * standard_normal_cdf(-d2)
    else:
        raise ValueError(f"Invalid option_type: '{option_type}'")


def all_greeks(
    spot: float,
    strike: float,
    rate: float,
    sigma: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
) -> dict[str, float]:
    """Calculate price and all five standard Greeks in a single call.

    Parameters
    ----------
    spot, strike, rate, sigma, time_to_maturity, option_type
        Standard Black-Scholes inputs.

    Returns
    -------
    dict[str, float]
        Dictionary with price, delta, gamma, vega, theta, and rho.
    """
    return {
        "price": black_scholes_price(spot, strike, rate, sigma, time_to_maturity, option_type),
        "delta": delta(spot, strike, rate, sigma, time_to_maturity, option_type),
        "gamma": gamma(spot, strike, rate, sigma, time_to_maturity),
        "vega": vega(spot, strike, rate, sigma, time_to_maturity),
        "theta": theta(spot, strike, rate, sigma, time_to_maturity, option_type),
        "rho": rho(spot, strike, rate, sigma, time_to_maturity, option_type),
    }


def implied_volatility(
    target_price: float,
    spot: float,
    strike: float,
    rate: float,
    time_to_maturity: float,
    option_type: Literal["call", "put"] = "call",
    initial_sigma: float = 0.20,
    tol: float = VOL_TOL,
    max_iter: int = MAX_ITER,
) -> float:
    """Solve for implied volatility using Newton-Raphson with Bisection fallback.

    Objective:
        Find sigma such that BlackScholes(S, K, r, sigma, T) - target_price = 0

    Parameters
    ----------
    target_price : float
        Observed market option price (> 0).
    spot : float
        Underlying spot price.
    strike : float
        Strike price.
    rate : float
        Risk-free rate.
    time_to_maturity : float
        Time to maturity in years.
    option_type : Literal['call', 'put']
        Option type.
    initial_sigma : float
        Initial starting guess for Newton-Raphson (default 0.20).
    tol : float
        Convergence tolerance on volatility.
    max_iter : int
        Maximum number of iterations.

    Returns
    -------
    float
        Implied annualized volatility.

    Raises
    ------
    ValueError
        If target price violates no-arbitrage lower/upper bounds.
    """
    discount = math.exp(-rate * time_to_maturity)
    opt = option_type.lower().strip()

    # Intrinsic / no-arbitrage lower bound check
    if opt == "call":
        intrinsic = max(0.0, spot - strike * discount)
        if target_price < intrinsic - 1e-7 or target_price >= spot:
            raise ValueError(
                f"Target call price {target_price:.4f} violates "
                f"arbitrage bounds [{intrinsic:.4f}, {spot:.4f}]"
            )
    elif opt == "put":
        intrinsic = max(0.0, strike * discount - spot)
        if target_price < intrinsic - 1e-7 or target_price >= strike * discount:
            raise ValueError(
                f"Target put price {target_price:.4f} violates "
                f"arbitrage bounds [{intrinsic:.4f}, {strike * discount:.4f}]"
            )

    sigma = initial_sigma

    # 1. Try Newton-Raphson (rapid quadratic convergence)
    for _ in range(max_iter):
        price = black_scholes_price(spot, strike, rate, sigma, time_to_maturity, opt)
        diff = price - target_price

        if abs(diff) < 1e-10:
            return sigma

        v = vega(spot, strike, rate, sigma, time_to_maturity)
        if v > 1e-8:
            sigma_new = sigma - diff / v
            if abs(sigma_new - sigma) < tol and sigma_new > 0:
                return sigma_new
            if 0.001 <= sigma_new <= 5.0:
                sigma = sigma_new
                continue

        # If Newton steps outside sane bounds or Vega is tiny, break to bisection
        break

    # 2. Bisection fallback
    low, high = 1e-4, 5.0
    for _ in range(max_iter * 2):
        mid = 0.5 * (low + high)
        mid_price = black_scholes_price(spot, strike, rate, mid, time_to_maturity, opt)
        diff = mid_price - target_price

        if abs(diff) < 1e-9 or (high - low) < tol:
            return mid

        if diff > 0:
            high = mid
        else:
            low = mid

    return 0.5 * (low + high)


def compute_option_surface(
    spot: float,
    strike: float,
    rate: float,
    sigmas: np.ndarray | list[float],
    maturities: np.ndarray | list[float],
    option_type: Literal["call", "put"] = "call",
) -> dict[str, np.ndarray]:
    """Compute price and Greeks across a 2D grid of volatilities and maturities.

    Parameters
    ----------
    spot : float
        Underlying spot price.
    strike : float
        Strike price.
    rate : float
        Risk-free interest rate.
    sigmas : np.ndarray | list[float]
        Array of annualized volatilities (rows).
    maturities : np.ndarray | list[float]
        Array of maturities in years (columns).
    option_type : Literal['call', 'put']
        Option type.

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary with 2D arrays (shape [len(sigmas), len(maturities)]) for:
        'price', 'delta', 'gamma', 'vega', 'theta', 'rho'.
    """
    sig_arr = np.asarray(sigmas, dtype=float)
    mat_arr = np.asarray(maturities, dtype=float)

    n_sig = len(sig_arr)
    n_mat = len(mat_arr)

    results = {
        "price": np.zeros((n_sig, n_mat), dtype=float),
        "delta": np.zeros((n_sig, n_mat), dtype=float),
        "gamma": np.zeros((n_sig, n_mat), dtype=float),
        "vega": np.zeros((n_sig, n_mat), dtype=float),
        "theta": np.zeros((n_sig, n_mat), dtype=float),
        "rho": np.zeros((n_sig, n_mat), dtype=float),
    }

    for i, s_val in enumerate(sig_arr):
        for j, t_val in enumerate(mat_arr):
            greeks = all_greeks(spot, strike, rate, float(s_val), float(t_val), option_type)
            for k in results:
                results[k][i, j] = greeks[k]

    return results

