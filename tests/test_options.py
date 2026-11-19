"""Tests for European option pricing, Greeks, and Implied Volatility engine.

Validates:
1. Hull textbook benchmark (S=42, K=40, r=0.10, sigma=0.20, T=0.5).
2. Put-call parity across a multi-dimensional parameter grid.
3. Theoretical bounds on Delta, Gamma, Vega, Theta, and Rho.
4. Greek numerical accuracy against central finite-difference approximations.
5. Implied volatility solver inversion accuracy and convergence.
6. Arbitrage bound validation and error handling.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.options import (
    all_greeks,
    black_scholes_price,
    compute_option_surface,
    delta,
    gamma,
    implied_volatility,
    rho,
    standard_normal_cdf,
    standard_normal_pdf,
    theta,
    vega,
)


def test_standard_normal_distribution():
    """Verify standard normal CDF and PDF symmetry and key quantile values."""
    assert math.isclose(standard_normal_cdf(0.0), 0.5, abs_tol=1e-12)
    assert math.isclose(standard_normal_pdf(0.0), 1.0 / math.sqrt(2.0 * math.pi), abs_tol=1e-12)

    # N(x) + N(-x) == 1
    for x in [-3.0, -1.96, -1.0, 0.5, 1.645, 2.58]:
        assert math.isclose(standard_normal_cdf(x) + standard_normal_cdf(-x), 1.0, abs_tol=1e-12)


def test_hull_textbook_benchmark():
    """Hull (Options, Futures, and Other Derivatives) Example:
    S = 42, K = 40, r = 10% (0.10), sigma = 20% (0.20), T = 0.5 years.
    Theoretical Call ~ 4.7594 (~4.76) and Put ~ 0.8086 (~0.81).
    """
    s = 42.0
    k = 40.0
    r = 0.10
    sigma = 0.20
    t = 0.5

    call_price = black_scholes_price(s, k, r, sigma, t, option_type="call")
    put_price = black_scholes_price(s, k, r, sigma, t, option_type="put")

    # Textbook rounded checks
    assert math.isclose(call_price, 4.76, abs_tol=0.01)
    assert math.isclose(put_price, 0.81, abs_tol=0.01)

    # High-precision analytical benchmark
    assert math.isclose(call_price, 4.75942, rel_tol=1e-4)
    assert math.isclose(put_price, 0.808599, rel_tol=1e-4)


def test_put_call_parity_grid():
    """Verify Put-Call Parity: C - P = S - K * exp(-r * T) holds across parameter grid.
    Tolerance: < 1e-10.
    """
    spots = [50.0, 100.0, 25000.0]
    rates = [0.01, 0.05, 0.10]
    sigmas = [0.10, 0.20, 0.40]
    maturities = [0.08, 0.25, 0.5, 1.0, 2.0]

    for s in spots:
        for k in [s * 0.9, s, s * 1.1]:
            for r in rates:
                for sig in sigmas:
                    for t in maturities:
                        call_p = black_scholes_price(s, k, r, sig, t, "call")
                        put_p = black_scholes_price(s, k, r, sig, t, "put")

                        lhs = call_p - put_p
                        rhs = s - k * math.exp(-r * t)
                        assert math.isclose(lhs, rhs, abs_tol=1e-10)


def test_greeks_bounds():
    """Verify analytical Greek properties and boundaries:
    - Call Delta in [0, 1]
    - Put Delta in [-1, 0]
    - Gamma >= 0
    - Vega >= 0
    """
    grid = [
        (42.0, 40.0, 0.10, 0.20, 0.5),
        (100.0, 100.0, 0.05, 0.15, 0.25),
        (25000.0, 25200.0, 0.065, 0.14, 30.0 / 365.0),
        (25000.0, 24000.0, 0.065, 0.25, 60.0 / 365.0),  # Deep ITM call / OTM put
        (25000.0, 26000.0, 0.065, 0.25, 60.0 / 365.0),  # Deep OTM call / ITM put
    ]

    for s, k, r, sig, t in grid:
        c_delta = delta(s, k, r, sig, t, "call")
        p_delta = delta(s, k, r, sig, t, "put")
        g = gamma(s, k, r, sig, t)
        v = vega(s, k, r, sig, t)

        assert 0.0 < c_delta < 1.0, f"Call delta {c_delta} out of (0, 1)"
        assert -1.0 < p_delta < 0.0, f"Put delta {p_delta} out of (-1, 0)"
        assert math.isclose(c_delta - p_delta, 1.0, abs_tol=1e-12)
        assert g > 0.0, f"Gamma {g} must be strictly positive"
        assert v > 0.0, f"Vega {v} must be strictly positive"


def test_greeks_finite_differences():
    """Verify analytical Greeks match numerical central finite-difference approximations.

    Central difference formulas:
        f'(x) ~ [f(x + h) - f(x - h)] / (2h)
        f''(x) ~ [f(x + h) - 2f(x) + f(x - h)] / h^2
    """
    s = 100.0
    k = 100.0
    r = 0.05
    sig = 0.20
    t = 0.5
    h = 1e-5

    # 1. Delta
    c_price_up = black_scholes_price(s + h, k, r, sig, t, "call")
    c_price_dn = black_scholes_price(s - h, k, r, sig, t, "call")
    fd_delta_call = (c_price_up - c_price_dn) / (2.0 * h)
    assert math.isclose(delta(s, k, r, sig, t, "call"), fd_delta_call, rel_tol=1e-5)

    p_price_up = black_scholes_price(s + h, k, r, sig, t, "put")
    p_price_dn = black_scholes_price(s - h, k, r, sig, t, "put")
    fd_delta_put = (p_price_up - p_price_dn) / (2.0 * h)
    assert math.isclose(delta(s, k, r, sig, t, "put"), fd_delta_put, rel_tol=1e-5)

    # 2. Gamma (second derivative wrt S)
    # Optimal step size h ~ eps^(1/4) ~ 1e-3 to prevent floating-point roundoff cancellation.
    h_gamma = 1e-3
    c_price_up_g = black_scholes_price(s + h_gamma, k, r, sig, t, "call")
    c_price_dn_g = black_scholes_price(s - h_gamma, k, r, sig, t, "call")
    c_price_mid = black_scholes_price(s, k, r, sig, t, "call")
    fd_gamma = (c_price_up_g - 2.0 * c_price_mid + c_price_dn_g) / (h_gamma * h_gamma)
    assert math.isclose(gamma(s, k, r, sig, t), fd_gamma, rel_tol=1e-5)

    # 3. Vega (derivative wrt sigma)
    h_vol = 1e-5
    c_vol_up = black_scholes_price(s, k, r, sig + h_vol, t, "call")
    c_vol_dn = black_scholes_price(s, k, r, sig - h_vol, t, "call")
    fd_vega = (c_vol_up - c_vol_dn) / (2.0 * h_vol)
    assert math.isclose(vega(s, k, r, sig, t), fd_vega, rel_tol=1e-5)

    # 4. Theta (- dV / dT)
    h_t = 1e-5
    c_t_up = black_scholes_price(s, k, r, sig, t + h_t, "call")
    c_t_dn = black_scholes_price(s, k, r, sig, t - h_t, "call")
    # By convention: Theta = dV / dt = - dV / dT
    fd_theta_call = -(c_t_up - c_t_dn) / (2.0 * h_t)
    assert math.isclose(theta(s, k, r, sig, t, "call"), fd_theta_call, rel_tol=1e-4)

    p_t_up = black_scholes_price(s, k, r, sig, t + h_t, "put")
    p_t_dn = black_scholes_price(s, k, r, sig, t - h_t, "put")
    fd_theta_put = -(p_t_up - p_t_dn) / (2.0 * h_t)
    assert math.isclose(theta(s, k, r, sig, t, "put"), fd_theta_put, rel_tol=1e-4)

    # 5. Rho (derivative wrt r)
    h_r = 1e-5
    c_r_up = black_scholes_price(s, k, r + h_r, sig, t, "call")
    c_r_dn = black_scholes_price(s, k, r - h_r, sig, t, "call")
    fd_rho_call = (c_r_up - c_r_dn) / (2.0 * h_r)
    assert math.isclose(rho(s, k, r, sig, t, "call"), fd_rho_call, rel_tol=1e-4)

    p_r_up = black_scholes_price(s, k, r + h_r, sig, t, "put")
    p_r_dn = black_scholes_price(s, k, r - h_r, sig, t, "put")
    fd_rho_put = (p_r_up - p_r_dn) / (2.0 * h_r)
    assert math.isclose(rho(s, k, r, sig, t, "put"), fd_rho_put, rel_tol=1e-4)


def test_implied_volatility_recovery():
    """Verify implied volatility solver accurately recovers known volatility."""
    test_cases = [
        (42.0, 40.0, 0.10, 0.20, 0.5, "call"),
        (42.0, 40.0, 0.10, 0.20, 0.5, "put"),
        (25000.0, 25200.0, 0.065, 0.145, 14.0 / 365.0, "call"),
        (25000.0, 25200.0, 0.065, 0.145, 14.0 / 365.0, "put"),
        (25000.0, 24500.0, 0.065, 0.320, 60.0 / 365.0, "call"),
        (25000.0, 25500.0, 0.065, 0.285, 30.0 / 365.0, "put"),
    ]

    for s, k, r, true_sig, t, opt in test_cases:
        price = black_scholes_price(s, k, r, true_sig, t, opt)
        recovered_sig = implied_volatility(price, s, k, r, t, opt)
        assert math.isclose(recovered_sig, true_sig, abs_tol=1e-6)


def test_implied_volatility_arbitrage_violation():
    """Verify solver raises ValueError if market price violates arbitrage bounds."""
    s = 100.0
    k = 90.0
    r = 0.05
    t = 1.0
    discount = math.exp(-r * t)
    intrinsic = s - k * discount

    # Call price below intrinsic bound
    with pytest.raises(ValueError, match="violates arbitrage bounds"):
        implied_volatility(intrinsic - 1.0, s, k, r, t, "call")

    # Call price exceeding spot bound
    with pytest.raises(ValueError, match="violates arbitrage bounds"):
        implied_volatility(s + 5.0, s, k, r, t, "call")


def test_all_greeks_and_surface():
    """Verify all_greeks dictionary and compute_option_surface grid dimensions."""
    s = 25000.0
    k = 25000.0
    r = 0.065
    sigmas = np.array([0.12, 0.16, 0.20])
    maturities = np.array([0.05, 0.10, 0.25, 0.50])

    greeks = all_greeks(s, k, r, 0.15, 0.25, "call")
    assert set(greeks.keys()) == {"price", "delta", "gamma", "vega", "theta", "rho"}
    assert greeks["price"] > 0
    assert 0 < greeks["delta"] < 1

    surface = compute_option_surface(s, k, r, sigmas, maturities, "call")
    assert surface["price"].shape == (3, 4)
    assert np.all(surface["price"] > 0)
    assert np.all(surface["vega"] > 0)
    assert np.all(surface["gamma"] > 0)
