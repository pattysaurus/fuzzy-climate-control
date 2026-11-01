import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---------- 1. INPUTS ----------
temp = ctrl.Antecedent(np.arange(16, 46, 1), "temperature")
hum = ctrl.Antecedent(np.arange(0, 101, 1), "humidity")
pas = ctrl.Antecedent(np.arange(1, 6, 1), "passengers")
fuel = ctrl.Antecedent(np.arange(0, 101, 1), "fuel_level")

# ---------- 2. OUTPUTS ----------
ac = ctrl.Consequent(np.arange(0, 101, 1), "ac_level")
blower = ctrl.Consequent(np.arange(0, 101, 1), "blower_speed")
recirc = ctrl.Consequent(np.arange(0, 101, 1), "recirculation")

# ---------- 3. MEMBERSHIP FUNCTIONS ----------
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

for var in (ac, blower, recirc):
    var["low"] = fuzz.trimf(var.universe, [0, 0, 50])
    var["medium"] = fuzz.trimf(var.universe, [25, 50, 75])
    var["high"] = fuzz.trimf(var.universe, [50, 100, 100])

# ---------- 4. RULES ----------
rules = [
    # Temperature is the main driver
    ctrl.Rule(temp["cool"], (ac["low"], blower["low"], recirc["low"])),
    ctrl.Rule(temp["comfortable"], (ac["low"], blower["low"], recirc["medium"])),
    ctrl.Rule(temp["hot"], (ac["high"], blower["high"], recirc["high"])),

    # Humidity: damp air needs more cooling to dehumidify
    ctrl.Rule(temp["comfortable"] & hum["high"], (ac["medium"], blower["medium"])),
    ctrl.Rule(temp["hot"] & hum["high"], (ac["high"], blower["high"])),
    ctrl.Rule(temp["hot"] & hum["low"], (ac["medium"], blower["medium"])),

    # Passengers: more people means more body heat
    ctrl.Rule(temp["comfortable"] & pas["many"], (ac["medium"], blower["medium"])),
    ctrl.Rule(temp["hot"] & pas["many"], (ac["high"], blower["high"])),
    ctrl.Rule(temp["hot"] & pas["few"], (ac["medium"], blower["medium"])),

    # Fuel level: eco mode when fuel is low (this is the fuel saving part)
    ctrl.Rule(fuel["low"] & temp["hot"], (ac["medium"], recirc["high"])),
    ctrl.Rule(fuel["low"] & temp["comfortable"], (ac["low"], blower["low"])),
    ctrl.Rule(fuel["high"] & temp["hot"], (ac["high"], blower["high"])),
]

system = ctrl.ControlSystem(rules)


def run(t, h, p, f):
    sim = ctrl.ControlSystemSimulation(system)
    sim.input["temperature"] = t
    sim.input["humidity"] = h
    sim.input["passengers"] = p
    sim.input["fuel_level"] = f
    sim.compute()
    return (sim.output["ac_level"], sim.output["blower_speed"],
            sim.output["recirculation"])


# ---------- 5. TEST SCENARIOS + FUEL SAVING ----------
# Assumption: a fixed AC runs at 100 percent. AC compressor takes about 3 kW
# at full level (assumed value).
# Engine fuel use is about 0.3 litre per kWh of engine output (assumed value).
COMPRESSOR_KW = 3.0
LITRE_PER_KWH = 0.3
TRIP_HOURS = 1.0

scenarios = [
    ("Cool morning, 2 people", 20, 40, 2, 70),
    ("Pleasant day, 1 person", 25, 50, 1, 60),
    ("Humid evening, 3 people", 28, 85, 3, 50),
    ("Hot afternoon, 4 people", 38, 40, 4, 80),
    ("Hot afternoon, low fuel", 38, 40, 4, 10),
    ("Very hot and humid, full car", 42, 90, 5, 60),
]

print(f"{'Scenario':32}{'AC':>6}{'Blower':>8}{'Recirc':>8}{'Fuel saved (L/hr)':>20}")
print("-" * 74)
total_saved = 0
for name, t, h, p, f in scenarios:
    a, b, r = run(t, h, p, f)
    fixed_fuel = COMPRESSOR_KW * 1.0 * LITRE_PER_KWH * TRIP_HOURS
    fuzzy_fuel = COMPRESSOR_KW * (a / 100) * LITRE_PER_KWH * TRIP_HOURS
    saved = fixed_fuel - fuzzy_fuel
    total_saved += saved
    print(f"{name:32}{a:6.1f}{b:8.1f}{r:8.1f}{saved:20.3f}")
print("-" * 74)
print(f"Average saving vs fixed full AC: {total_saved / len(scenarios):.3f} L/hr")

# ---------- 6. PLOTS ----------
fig, axes = plt.subplots(2, 3, figsize=(14, 7))
for ax, var, title in zip(axes.flat,
                          (temp, hum, pas, fuel, ac, recirc),
                          ("Temperature (C)", "Humidity (%)", "Passengers",
                           "Fuel level (%)", "AC / Blower output (%)",
                           "Recirculation (%)")):
    for term in var.terms:
        ax.plot(var.universe, var[term].mf, label=term)
    ax.set_title(title)
    ax.legend()
plt.tight_layout()
plt.savefig("membership_functions.png", dpi=120)
plt.close()

T, H = np.meshgrid(np.arange(16, 46, 2), np.arange(0, 101, 5))
Z = np.zeros_like(T, dtype=float)
for i in range(T.shape[0]):
    for j in range(T.shape[1]):
        Z[i, j] = run(T[i, j], H[i, j], 3, 50)[0]
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(T, H, Z, cmap="viridis")
ax.set_xlabel("Temperature (C)")
ax.set_ylabel("Humidity (%)")
ax.set_zlabel("AC level (%)")
ax.set_title("Control surface (3 passengers, 50% fuel)")
plt.savefig("control_surface.png", dpi=120)
plt.close()

labels = [s[0] for s in scenarios]
fuzzy_ac = [run(*s[1:])[0] for s in scenarios]
x = np.arange(len(labels))
plt.figure(figsize=(11, 5))
plt.bar(x - 0.2, [100] * len(labels), 0.4, label="Fixed AC (always full)")
plt.bar(x + 0.2, fuzzy_ac, 0.4, label="Fuzzy controller")
plt.xticks(x, labels, rotation=20, ha="right")
plt.ylabel("AC level (%)")
plt.title("AC usage: fixed vs fuzzy")
plt.legend()
plt.tight_layout()
plt.savefig("comparison.png", dpi=120)
print("Plots saved.")