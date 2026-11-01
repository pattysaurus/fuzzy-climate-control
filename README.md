# Multi-Variable Fuzzy Logic Climate Control System for Vehicle Fuel and Comfort Optimization

Soft Computing & Applications project, Amity School of Engineering and Technology (B.Tech CSE, Data Science).

A Mamdani fuzzy logic controller that sets a car's AC level, blower speed and air recirculation from four conditions, so the cabin stays comfortable while the AC uses less fuel than an always-full air conditioner.

## How it works

| | Variables |
|---|---|
| **Inputs (4)** | Cabin temperature (16-45 C), humidity (0-100 %), passengers (1-5), fuel level (0-100 %) |
| **Outputs (3)** | AC level, blower speed, recirculation (all 0-100 %) |
| **Method** | Mamdani inference, triangular and trapezoidal membership functions, centroid defuzzification |
| **Rules** | 12 IF-THEN rules, grouped by reason (temperature, humidity, passengers, fuel/eco) |

Fuel level works as an eco-priority: with low fuel the controller limits the AC.

## Run it

```
pip install -r requirements.txt
python fuzzy_climate_control.py
streamlit run app.py
```

- `fuzzy_climate_control.py` prints the results table for six test scenarios and saves the plots.
- `app.py` opens an interactive Streamlit dashboard with sliders, live outputs, the scenario table, membership functions, rules and a 3D control surface.

## Results

Compared with an AC that always runs at 100 %:

| Scenario | AC level | Fuel saved (L/hr) |
|---|---|---|
| Cool morning, 2 people | 16.7 % | 0.750 |
| Pleasant day, 1 person | 16.7 % | 0.750 |
| Humid evening, 3 people | 38.8 % | 0.551 |
| Hot afternoon, 4 people | 69.6 % | 0.274 |
| Hot afternoon, low fuel | 66.9 % | 0.298 |
| Very hot and humid, full car | 83.3 % | 0.150 |

Average saving: **0.462 L/hr**.

![Fixed vs fuzzy AC level](comparison.png)

## Assumptions and limitations

- The fuel model uses **assumed** values (3 kW compressor at full level, 0.3 L fuel per kWh), not measurements from a real vehicle. The litres saved are illustrative.
- The baseline is an AC that always runs at 100 %, which is the worst case. There is no comparison against an on/off thermostat or a PID controller.
- The controller maps inputs to outputs instantly. Cabin temperature over time is not simulated.
- Rules and membership functions were designed by hand, not tuned from data.

## Possible extensions

- Compare with on/off and PID controllers.
- Add a cabin thermal model.
- Tune the membership functions with a Genetic Algorithm or PSO.
- Add engine load or vehicle speed as an input.

## Files

| File | Purpose |
|---|---|
| `fuzzy_climate_control.py` | Controller, test scenarios and plots |
| `app.py` | Streamlit dashboard |
| `requirements.txt` | Python packages |
| `membership_functions.png`, `control_surface.png`, `comparison.png` | Generated plots |

## Tech

Python, scikit-fuzzy, NumPy, Matplotlib, pandas, Streamlit.
