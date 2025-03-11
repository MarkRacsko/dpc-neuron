import os
import pandas as pd
from matplotlib import figure

file: str = "./data/20250307/first measure ratio.xlsx"
dest_dir: str = "./data/20250307/plots/first measure"

input_df = pd.read_excel(file, sheet_name="ratio")
labels: list[str] = [col for col in input_df.columns if "Average" in col]

x_data, traces = input_df["Frame"], input_df[labels]
events: dict[int, str] = {
    60: "1 uM ATP",
    120: "",
    300: "40 uM PS",
    360: "",
    540: "100 uM AITC",
    600: "",
    780: "1 uM Capsaicin",
    840: "",
    1020: "50 mM KCl"
} # wash labels not included due to space constraints, but I still want vertical lines there
majors = [x for x in range(0, len(x_data) + 1, 60)]
major_labels = [str(x//60) for x in majors]

for i, col in enumerate(traces, start=1):
    y_data = traces[col]
    fig = figure.Figure(figsize=(10, 5))
    ax = fig.subplots(1, 1)

    ax.plot(x_data, y_data)
    ax.set_xticks(majors, labels=major_labels, minor=False)
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Ratio")

    ymin, ymax = ax.get_ylim()
    text_y = ymin - (ymax - ymin) * 0.2
    for time, event in events.items():
        ax.axvline(x=time, c="black")
        ax.text(x=time + 3, y=text_y, s=event)

    fig.suptitle(f"Neuron no. {i}")
    fig.tight_layout()
    fig.savefig(os.path.join(dest_dir, f"ROI {i}.png"), dpi=300)
    fig.clf()
    print(f"Done with {i}")