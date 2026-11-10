"""Biểu đồ đánh giá cho báo cáo (PNG, matplotlib).

Màu cố định theo thực thể (không đổi theo thứ hạng):
  LightGBM = xanh dương, Seasonal Naive = cam, MA-28 = xanh ngọc, Actual = xám đậm.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

COLORS = {"LightGBM": "#2a78d6", "Seasonal Naive": "#eb6834", "MA-28": "#1baf7a", "Actual": "#52514e"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.axisbelow": True, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "legend.frameon": False, "lines.linewidth": 2,
})


def _date_axis(ax):
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))


def _save(fig, paths):
    fig.tight_layout()
    for p in paths:
        fig.savefig(p, dpi=150)
    plt.close(fig)


def plot_model_comparison(overall: pd.DataFrame, paths):
    metrics = ["WAPE", "RMSE", "MAE"]
    models = [m for m in ["Seasonal Naive", "MA-28", "LightGBM"] if m in set(overall.model)]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, met in zip(axes, metrics):
        vals = [float(overall.loc[overall.model == m, met].iloc[0]) for m in models]
        bars = ax.bar(models, vals, color=[COLORS[m] for m in models], width=0.6, edgecolor=SURFACE, linewidth=2)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}{'%' if met == 'WAPE' else ''}",
                    ha="center", va="bottom", color=INK, fontsize=9)
        ax.set_title(met + (" (%)" if met == "WAPE" else " (đơn vị)"))
        ax.grid(axis="x", visible=False)
        ax.tick_params(axis="x", labelsize=9)
    fig.suptitle("So sánh mô hình trên backtest 4 fold (thấp hơn = tốt hơn)", color=INK, fontweight="bold")
    _save(fig, paths)


def plot_metric_by_horizon(by_h: pd.DataFrame, paths):
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for m in ["Seasonal Naive", "MA-28", "LightGBM"]:
        d = by_h[by_h.model == m].sort_values("horizon")
        if len(d):
            ax.plot(d.horizon, d.WAPE, marker="o", markersize=7, color=COLORS[m], label=m)
            ax.annotate(m, (d.horizon.iloc[-1], d.WAPE.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", color=MUTED, fontsize=9)
    ax.set_xlabel("Horizon (ngày tới)")
    ax.set_ylabel("WAPE (%)")
    ax.set_xticks(range(1, 8))
    ax.set_xlim(0.7, 8.2)
    ax.set_title("WAPE theo horizon dự báo")
    ax.legend(loc="upper left", ncol=3)
    _save(fig, paths)


def plot_wape_by_segment(seg: pd.DataFrame, paths):
    segs = list(dict.fromkeys(seg.segment))
    models = ["Seasonal Naive", "LightGBM"]
    x = np.arange(len(segs))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, m in enumerate(models):
        vals = [float(seg[(seg.segment == s) & (seg.model == m)].WAPE.iloc[0]) if
                len(seg[(seg.segment == s) & (seg.model == m)]) else np.nan for s in segs]
        ax.bar(x + (i - 0.5) * w, vals, w - 0.02, color=COLORS[m], label=m, edgecolor=SURFACE, linewidth=2)
    ax.set_xticks(x)
    ax.set_xticklabels(segs, fontsize=9)
    ax.set_ylabel("WAPE (%)")
    ax.set_title("WAPE theo nhóm SKU")
    ax.grid(axis="x", visible=False)
    ax.legend()
    _save(fig, paths)


def plot_actual_vs_pred(bt: pd.DataFrame, series: list[tuple[str, str]], names: dict, paths):
    fig, axes = plt.subplots(len(series), 1, figsize=(10, 2.6 * len(series)), sharex=True)
    axes = np.atleast_1d(axes)
    last_fold = bt.fold.max()
    for ax, (s, k) in zip(axes, series):
        d = bt[(bt.store_id == s) & (bt.sku_id == k) & (bt.horizon == 1) & (bt.fold == last_fold)].sort_values("target_date")
        ax.plot(d.target_date, d.y, color=COLORS["Actual"], label="Actual", linewidth=2)
        ax.plot(d.target_date, d.pred_seasonal_naive, color=COLORS["Seasonal Naive"], label="Seasonal Naive",
                linewidth=1.6, linestyle="--")
        ax.plot(d.target_date, d.pred_lightgbm, color=COLORS["LightGBM"], label="LightGBM", linewidth=2)
        so = d[d.y_ok == 0]
        if len(so):
            ax.scatter(so.target_date, so.y, s=40, facecolor=SURFACE, edgecolor="#e34948", zorder=5,
                       label="Stockout (loại khỏi đánh giá)")
        ax.set_title(f"{s} · {k} · {names.get(k, '')}", fontsize=10, loc="left")
        ax.set_ylabel("Số lượng")
        _date_axis(ax)
    axes[0].legend(loc="upper left", ncol=4, fontsize=8)
    fig.suptitle("Actual vs dự báo t+1 — fold backtest cuối", color=INK, fontweight="bold")
    _save(fig, paths)


def plot_feature_importance(imp: pd.Series, paths, top: int = 15, title="Feature importance (horizon 1)"):
    s = imp.head(top)[::-1]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.barh(s.index, s.values, color=COLORS["LightGBM"], height=0.6)
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    _save(fig, paths)


def plot_future_forecast(panel: pd.DataFrame, fc: pd.DataFrame, series, names, paths):
    fig, axes = plt.subplots(len(series), 1, figsize=(10, 2.5 * len(series)))
    axes = np.atleast_1d(axes)
    for ax, (s, k) in zip(axes, series):
        h = panel[(panel.store_id == s) & (panel.sku_id == k)].tail(28)
        f = fc[(fc.store_id == s) & (fc.sku_id == k)].sort_values("forecast_date")
        ax.plot(h.date, h.sales, color=COLORS["Actual"], label="Lịch sử 28 ngày")
        ax.plot(f.forecast_date, f.predicted_sales, color=COLORS["LightGBM"], marker="o", markersize=6,
                label="Dự báo 7 ngày")
        ax.axvline(h.date.max(), color=MUTED, linewidth=1, linestyle=":")
        ax.set_title(f"{s} · {k} · {names.get(k, '')}", fontsize=10, loc="left")
        _date_axis(ax)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Dự báo 7 ngày tới (10–16/11/2026)", color=INK, fontweight="bold")
    _save(fig, paths)


def plot_data_overview(panel: pd.DataFrame, paths):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [2.4, 1]})
    tot = panel.groupby("date")["sales"].sum(min_count=1)
    axes[0].plot(tot.index, tot.values, color=COLORS["LightGBM"], linewidth=1.2)
    axes[0].set_title("Tổng doanh số/ngày (3 cửa hàng)")
    axes[0].set_ylabel("Đơn vị")
    dow = panel.assign(d=panel.date.dt.dayofweek).groupby("d")["sales"].mean()
    axes[1].bar(["T2", "T3", "T4", "T5", "T6", "T7", "CN"], dow.values, color=COLORS["LightGBM"], width=0.6)
    axes[1].set_title("Trung bình theo thứ")
    axes[1].grid(axis="x", visible=False)
    _save(fig, paths)
