import streamlit as st
import numpy as np
import pandas as pd
from src.shared.ui import render_header
from src.derivatives.pricing_model import EuropeanOption, Stock
from src.derivatives.analytics import VanillaStrategy, plot_educational_profile, plot_vol_time_risk_profile, get_payoff_breakdown

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Options Strategy", page_icon="assets/logo.png", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .stButton button {height: 2.2rem; font-size: 0.8rem;}
        .stNumberInput input {height: 2rem;}
        .metric-label { font-size: 0.8rem; color: gray; margin-bottom: 0px; text-align: right; }
        .metric-value { font-size: 1.1rem; font-weight: bold; color: white; margin-top: 0px; text-align: right; }
        .market-context { color: #888; font-size: 0.85rem; margin-bottom: 15px; }
        .market-param { display: inline-block; margin-right: 25px; color: #666; font-size: 0.8rem; }
        .market-param b { color: #888; margin-left: 5px; }
    </style>
""", unsafe_allow_html=True)

render_header()

# --- MARKET CONTEXT HEADER ---
st.markdown(f"""
    <div class="market-context">
        <div style="font-weight: bold; margin-bottom: 2px;">Volatility: 20% | Rate: 3% | Dividend: 0% | Horizon: 30 Day</div>
    </div>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'strategy_legs' not in st.session_state:
    st.session_state.strategy_legs = [
        {'type': 'Call', 'action': 'Buy', 'strike': 100.0, 'qty': 1, 'expiry': 30}
    ]

if 'market_params' not in st.session_state:
    st.session_state.market_params = {
        'spot': 100.0,
        'vol': 0.20,
        'rate': 0.03,
        'div': 0.00
    }

if 'spot_slider' not in st.session_state:
    st.session_state.spot_slider = 100.0

if 'builder_version' not in st.session_state:
    st.session_state.builder_version = 0

# --- SYNC MARKET DATA ---
m_spot = float(st.session_state.spot_slider)
st.session_state.market_params['spot'] = m_spot
m_vol = st.session_state.market_params['vol']
m_rate = st.session_state.market_params['rate']
m_div = st.session_state.market_params['div']


# --- MAIN AREA: STRATEGY PRESETS ---
def apply_strategy_preset():
    sel = st.session_state.preset_selection
    s = st.session_state.spot_slider
    
    new_legs = []
    if sel == "Select Strategy":
        return
    elif sel == "Call":
        new_legs = [{'type': 'Call', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30}]
    elif sel == "Put":
        new_legs = [{'type': 'Put', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30}]
    elif sel == "Protective Put":
        new_legs = [
            {'type': 'Stock', 'action': 'Buy', 'strike': 100.0, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Buy', 'strike': s * 0.95, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Covered Call":
        new_legs = [
            {'type': 'Stock', 'action': 'Buy', 'strike': 100.0, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Sell', 'strike': s * 1.05, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Bull Call Spread":
        new_legs = [
            {'type': 'Call', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Sell', 'strike': s * 1.1, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Bull Put Spread":
        new_legs = [
            {'type': 'Put', 'action': 'Buy', 'strike': s * 0.9, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Sell', 'strike': s, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Bear Call Spread":
        new_legs = [
            {'type': 'Call', 'action': 'Sell', 'strike': s, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Buy', 'strike': s * 1.1, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Bear Put Spread":
        new_legs = [
            {'type': 'Put', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Sell', 'strike': s * 0.9, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Straddle":
        new_legs = [
            {'type': 'Call', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Strangle":
        new_legs = [
            {'type': 'Call', 'action': 'Buy', 'strike': s * 1.05, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Buy', 'strike': s * 0.95, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Butterfly":
        new_legs = [
            {'type': 'Call', 'action': 'Buy', 'strike': s * 0.95, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Sell', 'strike': s, 'qty': 2, 'expiry': 30},
            {'type': 'Call', 'action': 'Buy', 'strike': s * 1.05, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Iron Condor":
        new_legs = [
            {'type': 'Put', 'action': 'Sell', 'strike': s * 0.9, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Buy', 'strike': s * 0.85, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Sell', 'strike': s * 1.1, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Buy', 'strike': s * 1.15, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Box Spread":
        new_legs = [
            {'type': 'Call', 'action': 'Buy', 'strike': s * 0.95, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Sell', 'strike': s * 1.05, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Buy', 'strike': s * 1.05, 'qty': 1, 'expiry': 30},
            {'type': 'Put', 'action': 'Sell', 'strike': s * 0.95, 'qty': 1, 'expiry': 30}
        ]
    elif sel == "Calendar Spread":
        new_legs = [
            {'type': 'Call', 'action': 'Sell', 'strike': s, 'qty': 1, 'expiry': 30},
            {'type': 'Call', 'action': 'Buy', 'strike': s, 'qty': 1, 'expiry': 60}
        ]
    
    if new_legs:
        st.session_state.strategy_legs = new_legs
        st.session_state.builder_version += 1

preset_list = [
    "Select Strategy", "Call", "Put", "Protective Put", "Covered Call",
    "Bull Call Spread", "Bull Put Spread", "Bear Call Spread", "Bear Put Spread",
    "Straddle", "Strangle", "Butterfly", "Iron Condor", "Box Spread", "Calendar Spread", "Custom"
]

ps_col1, ps_col2 = st.columns([3, 1])
with ps_col1:
    sel = st.selectbox("Select a configuration to load", preset_list, key="preset_selection", label_visibility="collapsed")
with ps_col2:
    st.button("Apply Selected Strategy", use_container_width=True, on_click=apply_strategy_preset)

# --- MAIN AREA: STRATEGY BUILDER ---
st.subheader("Strategy Decomposition")
h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([1.5, 1.5, 2, 1.5, 2, 0.8])
with h_col1: st.caption("Action")
with h_col2: st.caption("Type")
with h_col3: st.caption("Strike")
with h_col4: st.caption("Qty")
with h_col5: st.caption("Expiry (Days)")

v = st.session_state.builder_version
new_legs_collector = []
for i, leg in enumerate(st.session_state.strategy_legs):
    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 2, 1.5, 2, 0.8])
    with c1:
        l_action = st.selectbox(f"A_{i}", ["Buy", "Sell"], index=0 if leg['action'] == 'Buy' else 1, key=f"action_{i}_{v}", label_visibility="collapsed")
    with c2:
        l_type = st.selectbox(f"T_{i}", ["Call", "Put", "Stock"], index=["Call", "Put", "Stock"].index(leg['type']), key=f"type_{i}_{v}", label_visibility="collapsed")
    with c3:
        l_strike = st.number_input(f"S_{i}", value=float(leg['strike']), step=1.0, key=f"strike_{i}_{v}", label_visibility="collapsed", disabled=(l_type == "Stock"))
    with c4:
        l_qty = st.number_input(f"Q_{i}", value=int(leg['qty']), min_value=1, key=f"qty_{i}_{v}", label_visibility="collapsed")
    with c5:
        l_expiry = st.number_input(f"E_{i}", value=int(leg['expiry']), min_value=1, key=f"expiry_{i}_{v}", label_visibility="collapsed")
    with c6:
        if st.button("X", key=f"remove_{i}_{v}"):
            st.session_state.strategy_legs.pop(i)
            st.session_state.builder_version += 1
            st.rerun()
    new_legs_collector.append({'action': l_action, 'type': l_type, 'strike': l_strike, 'qty': l_qty, 'expiry': l_expiry})

st.session_state.strategy_legs = new_legs_collector

if st.button("Add New Strategy Leg", use_container_width=True):
    st.session_state.strategy_legs.append({'type': 'Call', 'action': 'Buy', 'strike': m_spot, 'qty': 1, 'expiry': 30})
    st.session_state.builder_version += 1
    st.rerun()

if st.button("Flip Strategy Direction (Write Strategy)", use_container_width=True):
    for leg in st.session_state.strategy_legs:
        leg['action'] = "Sell" if leg['action'] == "Buy" else "Buy"
    st.session_state.builder_version += 1
    st.rerun()


# --- COMPUTATIONS ---
legs_objs = []
current_premium = 0.0

for leg in st.session_state.strategy_legs:
    q = leg['qty'] if leg['action'] == 'Buy' else -leg['qty']
    if leg['type'] == 'Stock':
        opt = Stock(S=m_spot)
    else:
        opt = EuropeanOption(S=m_spot, K=leg['strike'], T=leg['expiry']/365.0, r=m_rate, sigma=m_vol, q=m_div, option_type=leg['type'].lower())
    legs_objs.append((opt, q))
    current_premium += opt.price() * q

strategy = VanillaStrategy(legs_objs)
strikes = [leg['strike'] for leg in st.session_state.strategy_legs if leg['type'] != 'Stock']
if not strikes: strikes = [m_spot]
plot_range = [m_spot * 0.8, m_spot * 1.3]

# --- BREAKDOWN TABLE ---
df_breakdown = get_payoff_breakdown(strategy)
if df_breakdown is not None:
    st.write("---")
    st.subheader("Detailed Payoff")
    st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

# --- RESULTS DASHBOARD ---
st.divider()
col_spot1, col_spot2 = st.columns([3, 1])
with col_spot1:
    m_spot = st.slider("Underlying Spot (S)", min_value=50.0, max_value=150.0, key="spot_slider", step=0.5, format="%.1f")
with col_spot2:
    st.write(f"(Current Strategy Premium: **{current_premium:.2f} EUR**)")

res_col1, res_col2 = st.columns([5, 1])

with res_col2:
    st.markdown('<h3 style="text-align: right;">Live Greeks (Advanced)</h3>', unsafe_allow_html=True)
    g_vals = strategy.greeks()
    st.markdown(f'<p class="metric-label">Premium EUR</p><p class="metric-value">{current_premium:.2f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Live Delta</p><p class="metric-value">{g_vals["delta"]:.3f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Live Vega</p><p class="metric-value">{g_vals["vega"]:.3f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Live Gamma</p><p class="metric-value">{g_vals["gamma"]:.4f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Live Theta</p><p class="metric-value">{g_vals["theta"]:.3f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Type</p><p class="metric-value">{"Debit" if current_premium > 0 else "Credit"}</p>', unsafe_allow_html=True)

with res_col1:
    v_colA, v_colB = st.columns([1, 1])
    with v_colA:
        viz_mode = st.radio("Value Mode", ["Payoff (at maturity)", "P&L (incl. Premium)"], horizontal=True)
    with v_colB:
        greek_overlay = st.radio("Greek Overlay (Advanced)", ["None ", "Delta ", "Delta vs Gamma "], horizontal=True)
        
    show_pnl = (viz_mode == "P&L (incl. Premium)")
    fig_edu = plot_educational_profile(strategy, plot_range, show_pnl=show_pnl, overlay_type=greek_overlay, show_individual_legs=True)
    fig_edu.add_vline(x=m_spot, line_dash="solid", line_color="red", line_width=2)
    st.plotly_chart(fig_edu, use_container_width=True)

# --- VEGA & THETA ANALYSIS SECTION ---
st.divider()
st.subheader("Volatility & Time Analysis (Advanced)")
st.plotly_chart(plot_vol_time_risk_profile(strategy, plot_range), use_container_width=True)

# --- EDUCATIONAL FOOTER ---
exp_col1, exp_col2 = st.columns(2)
with exp_col1:
    st.markdown("### **Vega (Volatility Risk)**")
    st.markdown("""
    Vega measures how your strategy reacts to changes in implied volatility. **Long options profit from rising volatility**, 
    as higher uncertainty increases the theoretical odds of a payoff. Buying vanilla options means you are "Long Vega".
    """)
with exp_col2:
    st.markdown("### **Theta (Time Decay)**")
    st.markdown("""
    Theta represents the daily cost of holding your position. Options are wasting assets; they lose value every day 
    as they approach expiry. **Long positions suffer from Theta decay**, while sellers aim to capture this "time rent".
    """)
st.caption("Developed by Gwendal for M. Laurent Deville")
