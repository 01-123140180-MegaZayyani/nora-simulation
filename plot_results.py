"""
Plot iteration times and inferred triple counts.
"""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/iteration_times.csv")

fig, ax1 = plt.subplots(figsize=(8, 5))

color = "tab:blue"
ax1.set_xlabel("Iteration")
ax1.set_ylabel("Inferred triples", color=color)
ax1.bar(df["iteration"], df["inferred_triples"], color=color, alpha=0.6, label="Inferred triples")
ax1.tick_params(axis="y", labelcolor=color)

ax2 = ax1.twinx()
color = "tab:red"
ax2.set_ylabel("Time (seconds)", color=color)
ax2.plot(df["iteration"], df["time_seconds"], color=color, marker="o", label="Time")
ax2.tick_params(axis="y", labelcolor=color)

fig.tight_layout()
plt.title("NORA Simulation: Iterative Reasoning Performance")
plt.savefig("results/iteration_times.png", dpi=150)
print("Plot saved to results/iteration_times.png")