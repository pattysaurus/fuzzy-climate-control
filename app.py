import threading
import numpy as np
import pandas as pd
import streamlit as st
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.set_page_config(page_title="Fuzzy Climate Control", page_icon="🚗", layout="wide")

COMPRESSOR_KW = 3.0
LITRE_PER_KWH = 0.3


@st.cache_resource
def build_system():
    temp = ctrl.Antecedent(np.arange(16, 46, 1), "temperature")
    hum = ctrl.Antecedent(np.arange(0, 101, 1), "humidity")
    pas = ctrl.Antecedent(np.arange(1, 6, 1), "passengers")
    fuel = ctrl.Antecedent(np.arange(0, 101, 1), "fuel_level")
    ac = ctrl.Consequent(np.arange(0, 101, 1), "ac_level")
    blower = ctrl.Consequent(np.arange(0, 101, 1), "blower_speed")
    recirc = ctrl.Consequent(np.arange(0, 101, 1), "recirculation")

    temp["cool"] = fuzz.trapmf(temp.universe, [16, 16, 20, 25])
    temp["comfortable"] = fuzz.trimf(temp.universe, [21, 25, 31])
    temp["hot"] = fuzz.trapmf(temp.universe, [27, 36, 45, 45])
    hum["low"] = fuzz.trapmf(hum.universe, [0, 0, 30, 50])
    hum["medium"] = fuzz.trimf(hum.universe, [30, 50, 70])
    hum["high"] = fuzz.trapmf(hum.universe, [50, 70, 100, 100])
    pas["few"] = fuzz.trapmf(pas.universe, [1, 1, 1, 3])
    pas["some"] = fuzz.trimf(pas.universe, [2, 3, 4])
    pas["many"] = fuzz.trapmf(pas.universe, [3, 5, 5, 5])
    fuel["low"] = fuzz.trapmf(fuel.universe, [0, 0, 10, 30])
    fuel["medium"] = fuzz.trimf(fuel.universe, [20, 50, 80])
    fuel["high"] = fuzz.trapmf(fuel.universe, [60, 80, 100, 100])
    for v in (ac, blower, recirc):
        v["low"] = fuzz.trimf(v.universe, [0, 0, 50])
        v["medium"] = fuzz.trimf(v.universe, [25, 50, 75])
        v["high"] = fuzz.trimf(v.universe, [50, 100, 100])

    rules = [
        ctrl.Rule(temp["cool"], (ac["low"], blower["low"], recirc["low"])),
        ctrl.Rule(temp["comfortable"], (ac["low"], blower["low"], recirc["medium"])),
        ctrl.Rule(temp["hot"], (ac["high"], blower["high"], recirc["high"])),
        ctrl.Rule(temp["comfortable"] & hum["high"], (ac["medium"], blower["medium"])),
        ctrl.Rule(temp["hot"] & hum["high"], (ac["high"], blower["high"])),
        ctrl.Rule(temp["hot"] & hum["low"], (ac["medium"], blower["medium"])),
        ctrl.Rule(temp["comfortable"] & pas["many"], (ac["medium"], blower["medium"])),
        ctrl.Rule(temp["hot"] & pas["many"], (ac["high"], blower["high"])),
        ctrl.Rule(temp["hot"] & pas["few"], (ac["medium"], blower["medium"])),
        ctrl.Rule(fuel["low"] & temp["hot"], (ac["medium"], recirc["high"])),
        ctrl.Rule(fuel["low"] & temp["comfortable"], (ac["low"], blower["low"])),
        ctrl.Rule(fuel["high"] & temp["hot"], (ac["high"], blower["high"])),
    ]
    system = ctrl.ControlSystem(rules)
    return system, {"temp": temp, "hum": hum, "pas": pas, "fuel": fuel,
                    "ac": ac, "recirc": recirc}


@st.cache_resource
def get_lock():
    return threading.Lock()


SYSTEM, VARS = build_system()
LOCK = get_lock()

RULE_TEXT = [
    ("Temperature", "IF temperature is cool THEN AC low, blower low, recirculation low"),
    ("Temperature", "IF temperature is comfortable THEN AC low, blower low, recirculation medium"),
    ("Temperature", "IF temperature is hot THEN AC high, blower high, recirculation high"),
    ("Humidity", "IF comfortable AND humidity high THEN AC medium, blower medium"),
    ("Humidity", "IF hot AND humidity high THEN AC high, blower high"),
    ("Humidity", "IF hot AND humidity low THEN AC medium, blower medium"),
    ("Passengers", "IF comfortable AND passengers many THEN AC medium, blower medium"),
    ("Passengers", "IF hot AND passengers many THEN AC high, blower high"),
    ("Passengers", "IF hot AND passengers few THEN AC medium, blower medium"),
    ("Fuel (eco)", "IF fuel low AND hot THEN AC medium, recirculation high"),
    ("Fuel (eco)", "IF fuel low AND comfortable THEN AC low, blower low"),
    ("Fuel (eco)", "IF fuel high AND hot THEN AC high, blower high"),
]


def run(t, h, p, f):
    with LOCK:
        sim = ctrl.ControlSystemSimulation(SYSTEM)
        sim.input["temperature"] = t
        sim.input["humidity"] = h
        sim.input["passengers"] = p
        sim.input["fuel_level"] = f
        sim.compute()
        return (float(sim.output["ac_level"]), float(sim.output["blower_speed"]),
                float(sim.output["recirculation"]))


def fuel_saved(ac_level):
    return COMPRESSOR_KW * LITRE_PER_KWH * (1 - ac_level / 100)


st.title("🚗 Multi-Variable Fuzzy Logic Climate Control")
st.caption("Soft Computing Project | Vehicle fuel and comfort optimization")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🎛️ Live Controller", "📋 Scenarios", "📈 Membership Functions",
     "📜 Rules", "🌐 Control Surface"])

with tab1:
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Inputs")
        t = st.slider("Cabin temperature (°C)", 16.0, 45.0, 35.0, 0.5)
        h = st.slider("Humidity (%)", 0, 100, 60)
        p = st.slider("Passengers", 1, 5, 3)
        f = st.slider("Fuel level (%)", 0, 100, 50)

    a, b, r = run(t, h, p, f)
    with right:
        st.subheader("Fuzzy controller output")
        c1, c2, c3 = st.columns(3)
        c1.metric("❄️ AC level", f"{a:.0f}%")
        c2.metric("💨 Blower speed", f"{b:.0f}%")
        c3.metric("🔁 Recirculation", f"{r:.0f}%")
        c1.progress(int(a))
        c2.progress(int(b))
        c3.progress(int(r))

        st.subheader("Fuel comparison (per hour of driving)")
        fixed = COMPRESSOR_KW * LITRE_PER_KWH
        fuzzy = fixed * a / 100
        d1, d2, d3 = st.columns(3)
        d1.metric("Fixed AC (always full)", f"{fixed:.2f} L/hr")
        d2.metric("Fuzzy AC", f"{fuzzy:.2f} L/hr")
        d3.metric("Fuel saved", f"{fixed - fuzzy:.2f} L/hr",
                  delta=f"{(1 - a / 100) * 100:.0f}% saved")
        fig, ax = plt.subplots(figsize=(6, 2.2))
        ax.barh(["Fuzzy AC", "Fixed AC"], [fuzzy, fixed],
                color=["#2e9e5b", "#d9534f"])
        ax.set_xlabel("Fuel used by AC (L/hr)")
        ax.set_xlim(0, fixed * 1.1)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

with tab2:
    st.subheader("Test scenarios")
    scenarios = [
        ("Cool morning, 2 people", 20, 40, 2, 70),
        ("Pleasant day, 1 person", 25, 50, 1, 60),
        ("Humid evening, 3 people", 28, 85, 3, 50),
        ("Hot afternoon, 4 people", 38, 40, 4, 80),
        ("Hot afternoon, low fuel", 38, 40, 4, 10),
        ("Very hot and humid, full car", 42, 90, 5, 60),
    ]
    rows = []
    for name, t_, h_, p_, f_ in scenarios:
        a_, b_, r_ = run(t_, h_, p_, f_)
        rows.append({"Scenario": name, "Temp (°C)": t_, "Humidity (%)": h_,
                     "Passengers": p_, "Fuel (%)": f_,
                     "AC (%)": round(a_, 1), "Blower (%)": round(b_, 1),
                     "Recirc (%)": round(r_, 1),
                     "Fuel saved (L/hr)": round(fuel_saved(a_), 3)})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True)
    st.success(f"Average saving vs fixed full AC: "
               f"{df['Fuel saved (L/hr)'].mean():.3f} L/hr")
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(df))
    ax.bar(x - 0.2, [100] * len(df), 0.4, label="Fixed AC", color="#d9534f")
    ax.bar(x + 0.2, df["AC (%)"], 0.4, label="Fuzzy AC", color="#2e9e5b")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Scenario"], rotation=20, ha="right")
    ax.set_ylabel("AC level (%)")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Assumptions: compressor 3 kW at full level, 0.3 L fuel per kWh. "
               "These are rough values, not measurements.")

with tab3:
    st.subheader("Membership functions")
    items = [("Temperature (°C)", VARS["temp"]), ("Humidity (%)", VARS["hum"]),
             ("Passengers", VARS["pas"]), ("Fuel level (%)", VARS["fuel"]),
             ("AC / Blower output (%)", VARS["ac"]),
             ("Recirculation (%)", VARS["recirc"])]
    fig, axes = plt.subplots(2, 3, figsize=(14, 6))
    for ax, (title, var) in zip(axes.flat, items):
        for term in var.terms:
            ax.plot(var.universe, var[term].mf, label=term, linewidth=2)
        ax.set_title(title)
        ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

with tab4:
    st.subheader("The 12 rules in plain English")
    st.table(pd.DataFrame(RULE_TEXT, columns=["Group", "Rule"]))

@st.cache_data
def surface_data(sp, sf):
    T, H = np.meshgrid(np.arange(16, 46, 2), np.arange(0, 101, 5))
    Z = np.array([[run(T[i, j], H[i, j], sp, sf)[0]
                   for j in range(T.shape[1])] for i in range(T.shape[0])])
    return T, H, Z


with tab5:
    st.subheader("Control surface: AC level vs temperature and humidity")
    left5, right5 = st.columns([1, 1])
    with left5:
        sp = st.slider("Passengers", 1, 5, 3, key="sp")
        sf = st.slider("Fuel level (%)", 0, 100, 50, key="sf")
        st.caption("The surface shows how the AC level changes with temperature "
                   "and humidity for the chosen number of passengers and fuel level.")
    T, H, Z = surface_data(sp, sf)
    with right5:
        fig = plt.figure(figsize=(5.2, 4.0))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_surface(T, H, Z, cmap="viridis")
        ax.set_xlabel("Temperature (\u00b0C)")
        ax.set_ylabel("Humidity (%)")
        ax.set_title("Vertical axis: AC level (%)", fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)