"""STEP 7: forecast monthly UPI volume and compare against a simple baseline.

What it does
  1. Reads monthly volume from PostgreSQL.
  2. Baseline model : "seasonal naive + growth" (same month last year x latest YoY growth).
  3. Main model     : SARIMA on log(volume).
  4. Honest test    : rolling-origin backtest. Pretend it is 12 different past months,
                      forecast 3 months ahead each time, compare with what really happened.
  5. Forecasts the next 6 months with a 95% interval.
  6. Saves tables forecast_volume and forecast_eval to PostgreSQL (for Power BI)
     and a chart to docs/img/.

Run:  python src/forecast.py
"""
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from statsmodels.tsa.statespace.sarimax import SARIMAX

import config

warnings.filterwarnings("ignore")
HORIZON_TEST = 3      # months ahead used in the backtest
N_ORIGINS = 12        # how many past months we pretend to forecast from
HORIZON_FUTURE = 6    # months to forecast into the future


def baseline_forecast(y: pd.Series, h: int) -> np.ndarray:
    """same month last year x (latest 12-month growth ratio)"""
    ratio = y.iloc[-1] / y.iloc[-13]
    out = []
    for step in range(1, h + 1):
        out.append(y.iloc[-12 + (step - 1) % 12] * ratio)
    return np.array(out)


def sarima_fit(y: pd.Series):
    model = SARIMAX(np.log(y), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12),
                    enforce_stationarity=False, enforce_invertibility=False)
    return model.fit(disp=False)


def sarima_forecast(y: pd.Series, h: int):
    res = sarima_fit(y)
    fc = res.get_forecast(h)
    mean = np.exp(fc.predicted_mean.values)
    ci = np.exp(fc.conf_int(alpha=0.05).values)
    return mean, ci[:, 0], ci[:, 1]


def mape(actual, pred) -> float:
    actual, pred = np.asarray(actual), np.asarray(pred)
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)


def main() -> None:
    engine = create_engine(config.get_url())
    df = pd.read_sql("SELECT month, volume_mn FROM monthly_upi ORDER BY month", engine,
                     parse_dates=["month"])
    y = df.set_index("month")["volume_mn"].astype(float).asfreq("MS")
    if len(y) < 48:
        raise SystemExit("Need at least 48 months of data for this forecast.")

    # ---- backtest ---------------------------------------------------------------
    errs = {"baseline": [], "sarima": []}
    last_origin = len(y) - HORIZON_TEST
    for origin in range(last_origin - N_ORIGINS + 1, last_origin + 1):
        train, actual = y.iloc[:origin], y.iloc[origin:origin + HORIZON_TEST]
        errs["baseline"].append(mape(actual, baseline_forecast(train, HORIZON_TEST)))
        errs["sarima"].append(mape(actual, sarima_forecast(train, HORIZON_TEST)[0]))
    eval_df = pd.DataFrame({
        "model": ["Seasonal naive + growth (baseline)", "SARIMA (log)"],
        "mape_pct": [np.mean(errs["baseline"]), np.mean(errs["sarima"])],
        "horizon_months": HORIZON_TEST,
        "n_origins": N_ORIGINS,
    }).round(2)
    print("\nBacktest (lower MAPE = better):")
    print(eval_df.to_string(index=False))
    best = eval_df.loc[eval_df.mape_pct.idxmin(), "model"]
    print(f"-> Better model on this backtest: {best}")

    # ---- real forecast ----------------------------------------------------------
    mean, lo, hi = sarima_forecast(y, HORIZON_FUTURE)
    future_idx = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(1), periods=HORIZON_FUTURE, freq="MS")
    fc_df = pd.DataFrame({"month": future_idx, "model": "SARIMA (log)",
                          "forecast_mn": mean.round(1), "lower_95_mn": lo.round(1), "upper_95_mn": hi.round(1)})
    print("\nForecast:")
    print(fc_df.to_string(index=False))

    fc_df.to_sql("forecast_volume", engine, if_exists="replace", index=False)
    eval_df.to_sql("forecast_eval", engine, if_exists="replace", index=False)
    print("\n[ok] saved tables forecast_volume and forecast_eval to PostgreSQL")

    # ---- chart ------------------------------------------------------------------
    img_dir = config.ROOT / "docs" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    tail = y.iloc[-48:]
    ax.plot(tail.index, tail.values, label="Actual")
    ax.plot(future_idx, mean, "--", label="SARIMA forecast")
    ax.fill_between(future_idx, lo, hi, alpha=0.2, label="95% interval")
    ax.set_title("UPI monthly volume (million transactions)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(img_dir / "forecast_volume.png", dpi=150)
    print(f"[ok] chart saved to {img_dir / 'forecast_volume.png'}")


if __name__ == "__main__":
    main()
