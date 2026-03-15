import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.derivatives.pricing_model import EuropeanOption

class VanillaStrategy:
    """
    Representation of a multi-leg vanilla option strategy.
    """
    def __init__(self, legs):
        """
        :param legs: List of tuples (EuropeanOption, quantity)
        """
        self.legs = legs


    def greeks(self):
        agg_greeks = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}
        for opt, qty in self.legs:
            g = opt.greeks()
            for key in agg_greeks:
                agg_greeks[key] += g[key] * qty
        return agg_greeks

    def get_payoff(self, spots):
        total_payoff = np.zeros_like(spots)
        for opt, qty in self.legs:
            if opt.option_type == "call":
                total_payoff += np.maximum(spots - opt.K, 0) * qty
            elif opt.option_type == "put":
                total_payoff += np.maximum(opt.K - spots, 0) * qty
            elif opt.option_type == "stock":
                total_payoff += spots * qty
        return total_payoff



def plot_educational_profile(strategy, spot_range, show_pnl=False, overlay_type="Delta", show_individual_legs=False):
    spots = np.linspace(spot_range[0], spot_range[1], 200)
    payoff_at_mat = strategy.get_payoff(spots)
    total_premium = sum(opt.price() * qty for opt, qty in strategy.legs)
    offset = total_premium if show_pnl else 0.0
    y1_vals = payoff_at_mat - offset
    y1_label = "P&L (EUR)" if show_pnl else "Payoff (EUR)"
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Strategy Trace
    fig.add_trace(go.Scatter(x=spots, y=y1_vals, mode='lines', name=f"Total {y1_label}", line=dict(color='#00CC96', width=4)), secondary_y=False)
    
    # Individual Legs (only in Payoff mode)
    if show_individual_legs and not show_pnl:
        colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880']
        for idx, (opt, qty) in enumerate(strategy.legs):
            leg_payoff = np.zeros_like(spots)
            if opt.option_type == "call":
                leg_payoff = np.maximum(spots - opt.K, 0) * qty
            elif opt.option_type == "put":
                leg_payoff = np.maximum(opt.K - spots, 0) * qty
            elif opt.option_type == "stock":
                leg_payoff = spots * qty
            
            action_label = "Long" if qty > 0 else "Short"
            fig.add_trace(go.Scatter(
                x=spots, y=leg_payoff, mode='lines', 
                name=f"Leg {idx+1}: {action_label} {abs(qty)}x {opt.option_type.capitalize()} K={opt.K}",
                line=dict(width=1.5, dash='dot', color=colors[idx % len(colors)]),
                opacity=0.6
            ), secondary_y=False)

    y2_label = ""
    overlay_type = overlay_type.strip()
    if overlay_type != "None":
        deltas, gammas = [], []
        for s in spots:
            d, g = 0, 0
            for opt, qty in strategy.legs:
                orig_S = opt.S
                opt.S = s
                if overlay_type in ["Delta", "Delta vs Gamma"]: d += opt.delta() * qty
                if overlay_type == "Delta vs Gamma": g += opt.gamma() * qty
                opt.S = orig_S
            deltas.append(d)
            gammas.append(g)
            
        if overlay_type == "Delta":
            fig.add_trace(go.Scatter(x=spots, y=deltas, mode='lines', name='Delta', line=dict(color='#1f77b4', width=2, dash='dot')), secondary_y=True)
            y2_label = "Delta"
        elif overlay_type == "Delta vs Gamma":
            fig.add_trace(go.Scatter(x=spots, y=deltas, mode='lines', name='Delta', line=dict(color='#1f77b4', width=2, dash='dot')), secondary_y=True)
            fig.add_trace(go.Scatter(x=spots, y=gammas, mode='lines', name='Gamma', line=dict(color='#ff7f0e', width=2, dash='dash')), secondary_y=True)
            y2_label = "Delta & Gamma"

    fig.update_layout(
        title=f"Strategy {y1_label} Profile",
        xaxis_title="Underlying Price",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text=y1_label, secondary_y=False)
    fig.update_yaxes(title_text=y2_label, secondary_y=True, showgrid=False)
    return fig

def plot_vol_time_risk_profile(strategy, spot_range):
    spots = np.linspace(spot_range[0], spot_range[1], 200)
    vega_vals, theta_vals = [], []
    for s in spots:
        v, t = 0, 0
        for opt, qty in strategy.legs:
            orig_S = opt.S
            opt.S = s
            v += opt.vega_point() * qty
            t += opt.daily_theta() * qty
            opt.S = orig_S
        vega_vals.append(v)
        theta_vals.append(t)
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spots, y=vega_vals, mode='lines', name='Vega (EUR / +1% vol)', line=dict(color='#2ca02c', width=3), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=spots, y=theta_vals, mode='lines', name='Daily Theta (EUR / day)', line=dict(color='#d62728', width=2, dash='dot')))
    fig.update_layout(
        title="Volatility Risk (Vega) vs Time Decay (Theta)",
        xaxis_title="Underlying Price",
        yaxis_title="Risk Amount (EUR)",
        template="plotly_dark",
        hovermode="x unified",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.add_hline(y=0, line_color="gray", line_width=1, opacity=0.5)
    return fig

def get_payoff_breakdown(strategy):
    """
    Returns a dataframe-ready dictionary representing the payoff of each leg
    across different spot price intervals defined by unique strikes.
    """
    strikes = sorted(list(set(opt.K for opt, _ in strategy.legs if opt.K is not None)))
    if not strikes:
        # If only stock, define a single wide interval
        intervals = ["ST (Full Range)"]
    else:
        intervals = []
        # Define interval labels
        intervals.append(f"ST < {strikes[0]}")
        for i in range(len(strikes)-1):
            intervals.append(f"{strikes[i]} < ST < {strikes[i+1]}")
        intervals.append(f"ST > {strikes[-1]}")
    
    rows = []
    # For each leg, calculate expression in each interval
    for idx, (opt, qty) in enumerate(strategy.legs):
        leg_label = f"{opt.option_type.capitalize()} K={opt.K}"
        leg_exprs = []
        
        for j in range(len(intervals)):
            # Midpoint/Sample point for logic
            if j == 0:
                s_test = strikes[0] - 5
            elif j == len(intervals) - 1:
                s_test = strikes[-1] + 5
            else:
                s_test = (strikes[j-1] + strikes[j]) / 2
                
            # Logic to determine expression string
            mult = "" if qty == 1 else ("-" if qty == -1 else f"{qty} * ")
            if opt.option_type == "call":
                if s_test < opt.K:
                    expr = "0"
                else:
                    expr = f"{mult}(ST - {opt.K})"
            elif opt.option_type == "put":
                if s_test > opt.K:
                    expr = "0"
                else:
                    expr = f"{mult}({opt.K} - ST)"
            elif opt.option_type == "stock":
                expr = f"{mult}ST"
            leg_exprs.append(expr)
        
        rows.append({"Component": leg_label, **dict(zip(intervals, leg_exprs))})
        
    # Total Payoff row 
    total_data = {"Component": "TOTAL PAYOFF"}
    for interval in intervals:
        comp_exprs = [r[interval] for r in rows if r[interval] != "0"]
        if not comp_exprs:
            total_data[interval] = "0"
        else:
            # Join non-zero expressions
            total_data[interval] = " + ".join(comp_exprs).replace("+ -", "- ")
    rows.append(total_data)

    import pandas as pd
    return pd.DataFrame(rows)
