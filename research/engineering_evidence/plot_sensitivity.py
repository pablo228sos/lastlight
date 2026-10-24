"""Plot only saved official-engine results; no physics calculation in this file."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]


def main():
    with (ROOT / "docs/research/data/sensitivity_results.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = [
            r
            for r in csv.DictReader(stream)
            if r["role"] == "study" and r["horizon_hours"] == "32"
        ]
    assert len(rows) == 12
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "svg.fonttype": "none",
            "svg.hashsalt": "LASTLIGHT-sensitivity-v1",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.5), sharex=True, sharey=True)
    colors = {24: "#15786f", 36: "#d98c28"}
    loads = [0.75, 1.5, 3.0]
    for ax, soc in zip(axes, [0.4, 0.8]):
        for capacity, offset in [(24, -0.18), (36, 0.18)]:
            values = [
                float(
                    next(
                        r
                        for r in rows
                        if float(r["capacity_kwh"]) == capacity
                        and float(r["initial_soc"]) == soc
                        and float(r["critical_load_kw"]) == load
                    )["observed_first_failure_hours"]
                )
                for load in loads
            ]
            y = [i + offset for i in range(3)]
            ax.barh(y, values, height=0.30, color=colors[capacity])
            for yy, value in zip(y, values):
                ax.text(
                    value + 0.3,
                    yy,
                    f"{value:.2f}".replace(".", ","),
                    va="center",
                    fontsize=12,
                )
        ax.axvline(12, color="#944743", ls="--", lw=1.6, zorder=0)
        ax.set_title(f"Начальный SOC {soc:.0%}", fontsize=15, pad=14)
        ax.set_xlim(0, 31)
        ax.set_xticks([0, 6, 12, 18, 24, 30])
        ax.set_yticks(range(3), ["0,75 кВт", "1,5 кВт", "3,0 кВт"])
        ax.grid(axis="x", color="#d9dedb", lw=0.65)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_ylabel("Критическая нагрузка", labelpad=13)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Как нагрузка и начальный заряд меняют автономность",
        fontsize=19,
        x=0.50,
        y=0.965,
    )
    fig.legend(
        handles=[
            Patch(color=colors[24], label="Батарея 24 кВт·ч"),
            Patch(color=colors[36], label="Батарея 36 кВт·ч"),
            Line2D([0], [0], color="#944743", ls="--", label="Окно отключения 12 ч"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.91),
        ncol=3,
        frameon=False,
        fontsize=12,
    )
    fig.supxlabel(
        "Наблюдаемый первый дефицит критической нагрузки, часы", y=0.14, fontsize=13
    )
    fig.text(
        0.5,
        0.055,
        "LASTLIGHT 1.0.0 · горизонт расчёта 32 ч · PV = 0 · резерв SOC 20% · КПД разряда 95%\nСинтетические сценарии постоянной нагрузки; не измерения школы и не вероятность отключения.",
        ha="center",
        va="center",
        fontsize=10,
        color="#4c5753",
    )
    fig.subplots_adjust(left=0.12, right=0.965, top=0.73, bottom=0.25, wspace=0.14)
    out = ROOT / "docs/research/figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out / "sensitivity_autonomy_ru.png",
        dpi=160,
        facecolor="white",
        metadata={"Software": "LASTLIGHT engineering evidence; official model 1.0.0"},
    )
    fig.savefig(
        out / "sensitivity_autonomy_ru.svg",
        facecolor="white",
        metadata={"Date": None, "Creator": "LASTLIGHT engineering evidence"},
    )
    svg = out / "sensitivity_autonomy_ru.svg"
    svg.write_text(
        "\n".join(
            line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    plt.close(fig)
    print("Saved PNG and SVG from 12 observed 32-hour engine results")


if __name__ == "__main__":
    main()
