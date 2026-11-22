"""
Satellite camera debris-tracking simulation (500 scenarios, bearing 90 deg (E) -> 180 deg (S), SE = 135 deg)

Frame: satellite-centred local frame, x = East, y = North, z = Up (km, km/s).
Short-window relative motion is treated as a straight line (valid for seconds-minutes).

Camera model (angles-only + apparent-size range):
  - measures azimuth/elevation of debris (pixel/IFOV noise)
  - range from apparent angular size of debris of known approx diameter (noisy)
Estimator: least-squares line fit to the 3-D position track -> position, velocity,
closing speed, time to closest approach (TCA), miss distance.
"""
import numpy as np, csv

rng = np.random.default_rng(42)
N_SCEN   = 500
FPS_DT   = 1.0          # one camera frame per second
N_FRAMES = 60           # observation window (s)
ANG_SIGMA = np.radians(0.005)   # 0.005 deg angular noise (~90 urad)
RANGE_SIGMA_FRAC = 0.005        # 0.5 % range error (size + stereo/ranging aid)
HIT_RADIUS = 0.1        # km  (100 m keep-out) -> collision flag
WARN_RADIUS = 1.0       # km  -> warning flag

# bearings spread evenly 270..360 deg (West -> NW -> North), compass convention
bearings = np.linspace(90, 180, N_SCEN)

def compass_to_unit(az_deg, el_deg):
    az, el = np.radians(az_deg), np.radians(el_deg)
    return np.array([np.sin(az)*np.cos(el),   # East
                     np.cos(az)*np.cos(el),   # North
                     np.sin(el)])             # Up

rows = []
for i, brg in enumerate(bearings):
    # ---- truth ----
    el0   = rng.uniform(-20, 20)                 # elevation of debris
    r0    = rng.uniform(1000, 2000)              # initial range (km)
    p0    = r0 * compass_to_unit(brg, el0)       # position at t=0
    closing = rng.uniform(0.5, 14.0)             # km/s closing speed
    # aim point: offset from satellite -> controls miss distance
    miss_aim = rng.uniform(0, 2.0) * rng.normal(size=3)
    aim_dir  = (miss_aim - p0); aim_dir /= np.linalg.norm(aim_dir)
    v_true   = closing * aim_dir                 # relative velocity (km/s)

    t = np.arange(N_FRAMES) * FPS_DT
    P_true = p0[None, :] + t[:, None] * v_true[None, :]

    # ---- camera measurement ----
    r_true = np.linalg.norm(P_true, axis=1)
    az_true = np.degrees(np.arctan2(P_true[:, 0], P_true[:, 1])) % 360
    el_true = np.degrees(np.arcsin(P_true[:, 2] / r_true))
    az_m = np.radians(az_true) + rng.normal(0, ANG_SIGMA, N_FRAMES)
    el_m = np.radians(el_true) + rng.normal(0, ANG_SIGMA, N_FRAMES)
    r_m  = r_true * (1 + rng.normal(0, RANGE_SIGMA_FRAC, N_FRAMES))
    P_meas = np.c_[r_m*np.sin(az_m)*np.cos(el_m),
                   r_m*np.cos(az_m)*np.cos(el_m),
                   r_m*np.sin(el_m)]

    # ---- estimation: linear fit per axis ----
    A = np.c_[np.ones_like(t), t]
    coef, *_ = np.linalg.lstsq(A, P_meas, rcond=None)
    p_est, v_est = coef[0], coef[1]
    # estimated state at last frame
    p_now = p_est + v_est * t[-1]
    r_now = np.linalg.norm(p_now)
    speed_rel = np.linalg.norm(v_est)
    closing_est = -np.dot(p_now, v_est) / r_now           # + = approaching
    t_ca = -np.dot(p_now, v_est) / np.dot(v_est, v_est)   # s from last frame
    miss_est = np.linalg.norm(p_now + v_est * max(t_ca, 0))

    # truth for comparison
    p_last = P_true[-1]
    t_ca_true = -np.dot(p_last, v_true) / np.dot(v_true, v_true)
    miss_true = np.linalg.norm(p_last + v_true * max(t_ca_true, 0))

    az_est = np.degrees(np.arctan2(p_now[0], p_now[1])) % 360
    el_est = np.degrees(np.arcsin(p_now[2] / r_now))
    sector = ("South" if brg >= 157.5 else "South-East" if brg >= 112.5 else "East")
    status = ("COLLISION RISK" if (miss_est < HIT_RADIUS and t_ca > 0) else
              "WARNING" if (miss_est < WARN_RADIUS and t_ca > 0) else
              "SAFE" if t_ca > 0 else "RECEDING")

    rows.append(dict(
        scenario=i+1, sector=sector, bearing_true_deg=round(az_true[-1], 3),
        bearing_est_deg=round(az_est, 3), elevation_est_deg=round(el_est, 3),
        range_true_km=round(r_true[-1], 3), range_est_km=round(r_now, 3),
        closing_true_kms=round(closing, 3), closing_est_kms=round(closing_est, 3),
        closing_err_pct=round(100*(closing_est-closing)/closing, 2),
        rel_speed_est_kms=round(speed_rel, 3),
        tca_true_s=round(t_ca_true, 2), tca_est_s=round(t_ca, 2),
        miss_true_km=round(miss_true, 3), miss_est_km=round(miss_est, 3),
        status=status))

with open("debris_scenarios_south_to_east.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

# ---- summary ----
import collections
err = np.array([r["closing_err_pct"] for r in rows])
print(f"Scenarios: {len(rows)}   bearing range: {bearings[0]:.0f}-{bearings[-1]:.0f} deg")
print(f"Closing-speed error: mean {err.mean():.2f}%  |abs| median {np.median(abs(err)):.2f}%  95th {np.percentile(abs(err),95):.2f}%")
print("Status counts:", dict(collections.Counter(r['status'] for r in rows)))
for s in ("East", "South-East", "South"):
    sub = [r for r in rows if r["sector"] == s]
    print(f"{s:11s} n={len(sub):3d}  mean closing {np.mean([r['closing_true_kms'] for r in sub]):.2f} km/s  "
          f"risk={sum(r['status']=='COLLISION RISK' for r in sub)}  warn={sum(r['status']=='WARNING' for r in sub)}")

# ---- optional plot ----
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    b = [r["bearing_true_deg"] for r in rows]
    c = {"COLLISION RISK": "red", "WARNING": "orange", "SAFE": "green", "RECEDING": "gray"}
    ax[0].scatter(b, [r["closing_est_kms"] for r in rows], c=[c[r["status"]] for r in rows], s=10)
    ax[0].set(xlabel="Debris bearing (deg)  E=90  SE=135  S=180", ylabel="Estimated closing speed (km/s)",
              title="Closing speed vs bearing")
    ax[1].scatter([r["closing_true_kms"] for r in rows], [r["closing_est_kms"] for r in rows], s=8)
    ax[1].plot([0, 15], [0, 15], "k--"); ax[1].set(xlabel="True (km/s)", ylabel="Estimated (km/s)", title="Estimator accuracy")
    plt.tight_layout(); plt.savefig("debris_plot_south_to_east.png", dpi=120)
except ImportError:
    pass
