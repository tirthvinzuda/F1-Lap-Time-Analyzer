"""F1 Lap Time Analyzer

Compares the lap times of two drivers:
  - fastest lap
  - average lap time
  - difference between drivers
  - consistency (standard deviation)
  - lap-time graph

Usage:
    python main.py                  # interactive menu
    python main.py --csv lap_times.csv
    python main.py --sample --no-show
"""

import argparse
import csv
import statistics
import sys

import matplotlib.pyplot as plt

GRAPH_FILE = "lap_time_graph.png"

# Sample data (seconds), used when no CSV / manual input is chosen
SAMPLE_A = [90.2, 89.8, 90.5, 89.9, 90.1]
SAMPLE_B = [90.0, 90.4, 89.7, 91.2, 90.3]


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def validate_laps(laps, name):
    """Return a clean list of floats or raise ValueError with a clear message."""
    if not laps:
        raise ValueError(f"{name} has no lap times.")
    cleaned = []
    for i, value in enumerate(laps, start=1):
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name}, lap {i}: '{value}' is not a number.")
        if number != number or number in (float("inf"), float("-inf")):
            raise ValueError(f"{name}, lap {i}: value is not a finite number.")
        if number <= 0:
            raise ValueError(f"{name}, lap {i}: lap time must be positive (got {number}).")
        cleaned.append(number)
    return cleaned


def validate_pair(laps_a, laps_b, name_a, name_b):
    a = validate_laps(laps_a, name_a)
    b = validate_laps(laps_b, name_b)
    if len(a) != len(b):
        raise ValueError(
            f"Both drivers need the same number of laps ({name_a}: {len(a)}, {name_b}: {len(b)})."
        )
    return a, b


# --------------------------------------------------------------------------
# Analysis functions
# --------------------------------------------------------------------------
def fastest_lap(laps):
    """Return (best_time, lap_number)."""
    best = min(laps)
    return best, laps.index(best) + 1


def slowest_lap(laps):
    worst = max(laps)
    return worst, laps.index(worst) + 1


def average_lap(laps):
    return sum(laps) / len(laps)


def compare_averages(avg_a, avg_b, name_a, name_b):
    """Return (faster_driver_or_None, difference_in_seconds)."""
    diff = abs(avg_a - avg_b)
    if avg_a < avg_b:
        return name_a, diff
    elif avg_b < avg_a:
        return name_b, diff
    return None, 0.0


def consistency(laps_a, laps_b, name_a, name_b):
    """Lower population standard deviation = more consistent."""
    sd_a = statistics.pstdev(laps_a)
    sd_b = statistics.pstdev(laps_b)
    if sd_a < sd_b:
        winner = name_a
    elif sd_b < sd_a:
        winner = name_b
    else:
        winner = None
    return sd_a, sd_b, winner


def unusually_slow_laps(laps, threshold=1.5):
    """Laps slower than mean + threshold * stdev (needs >= 3 laps and some spread)."""
    if len(laps) < 3:
        return []
    sd = statistics.pstdev(laps)
    if sd == 0:
        return []
    limit = statistics.mean(laps) + threshold * sd
    return [(i + 1, t) for i, t in enumerate(laps) if t > limit]


# --------------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------------
def plot_laps(laps_a, laps_b, name_a, name_b, save_path=GRAPH_FILE, show=True):
    lap_numbers = list(range(1, len(laps_a) + 1))
    avg_a, avg_b = average_lap(laps_a), average_lap(laps_b)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(lap_numbers, laps_a, marker="o", color="tab:red", label=name_a)
    ax.plot(lap_numbers, laps_b, marker="s", color="tab:blue", label=name_b)

    # Average reference lines
    ax.axhline(avg_a, color="tab:red", linestyle="--", alpha=0.5, label=f"{name_a} avg")
    ax.axhline(avg_b, color="tab:blue", linestyle="--", alpha=0.5, label=f"{name_b} avg")

    # Mark each driver's fastest lap
    best_a, lap_a = fastest_lap(laps_a)
    best_b, lap_b = fastest_lap(laps_b)
    ax.scatter([lap_a], [best_a], s=200, facecolors="none", edgecolors="tab:red", linewidths=2)
    ax.scatter([lap_b], [best_b], s=200, facecolors="none", edgecolors="tab:blue", linewidths=2)
    ax.annotate(f"Best {best_a:.2f}", (lap_a, best_a), textcoords="offset points",
                xytext=(0, -20), ha="center", color="tab:red")
    ax.annotate(f"Best {best_b:.2f}", (lap_b, best_b), textcoords="offset points",
                xytext=(0, -20), ha="center", color="tab:blue")

    ax.set_title(f"Lap Time Comparison: {name_a} vs {name_b}")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time (seconds)")
    ax.set_xticks(lap_numbers if len(lap_numbers) <= 20 else ax.get_xticks())
    ax.margins(y=0.12)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------
def read_csv(path):
    """CSV columns: lap, <driver A name>, <driver B name>. Returns (name_a, name_b, laps_a, laps_b)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 3:
            raise ValueError("CSV needs 3 columns: lap, driver A, driver B.")
        name_a, name_b = header[1].strip(), header[2].strip()
        laps_a, laps_b = [], []
        for row_num, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue  # skip blank lines
            if len(row) < 3 or not row[1].strip() or not row[2].strip():
                raise ValueError(f"CSV row {row_num}: missing lap time.")
            laps_a.append(row[1].strip())
            laps_b.append(row[2].strip())
    return name_a, name_b, laps_a, laps_b


def ask_laps(name, count):
    laps = []
    for i in range(1, count + 1):
        while True:
            raw = input(f"  {name} - lap {i} time (seconds): ").strip()
            try:
                value = float(raw)
                if value <= 0:
                    raise ValueError
                laps.append(value)
                break
            except ValueError:
                print("  Please enter a positive number, e.g. 90.25")
    return laps


def manual_input():
    name_a = input("Driver A name: ").strip() or "Driver A"
    name_b = input("Driver B name: ").strip() or "Driver B"
    while True:
        try:
            count = int(input("How many laps to compare? ").strip())
            if count > 0:
                break
        except ValueError:
            pass
        print("Please enter a whole number greater than 0.")
    return name_a, name_b, ask_laps(name_a, count), ask_laps(name_b, count)


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def print_report(laps_a, laps_b, name_a, name_b, graph_path):
    best_a, best_lap_a = fastest_lap(laps_a)
    best_b, best_lap_b = fastest_lap(laps_b)
    worst_a, _ = slowest_lap(laps_a)
    worst_b, _ = slowest_lap(laps_b)
    avg_a, avg_b = average_lap(laps_a), average_lap(laps_b)
    faster, diff = compare_averages(avg_a, avg_b, name_a, name_b)
    sd_a, sd_b, steady = consistency(laps_a, laps_b, name_a, name_b)

    line = "=" * 52
    print(f"\n{line}\n  F1 LAP TIME ANALYSIS\n{line}")
    print(f"Laps analyzed: {len(laps_a)}\n")

    print("FASTEST LAP")
    print(f"  {name_a}: {best_a:.2f}s (lap {best_lap_a})")
    print(f"  {name_b}: {best_b:.2f}s (lap {best_lap_b})")
    if best_a < best_b:
        print(f"  -> {name_a} set the faster lap")
    elif best_b < best_a:
        print(f"  -> {name_b} set the faster lap")
    else:
        print("  -> Both drivers set the same fastest lap")

    print("\nAVERAGE LAP TIME")
    print(f"  {name_a}: {avg_a:.2f}s")
    print(f"  {name_b}: {avg_b:.2f}s")
    print(f"  Difference: {diff:.2f}s")
    print(f"  -> Faster on average: {faster or 'Tie'}")

    print("\nSLOWEST LAP / RANGE")
    print(f"  {name_a}: {worst_a:.2f}s (range {worst_a - best_a:.2f}s)")
    print(f"  {name_b}: {worst_b:.2f}s (range {worst_b - best_b:.2f}s)")

    print("\nCONSISTENCY (standard deviation, lower = steadier)")
    print(f"  {name_a}: {sd_a:.3f}s")
    print(f"  {name_b}: {sd_b:.3f}s")
    print(f"  -> More consistent: {steady or 'Tie'}")

    print("\nLAP-BY-LAP WINNER")
    wins_a = wins_b = 0
    for i, (a, b) in enumerate(zip(laps_a, laps_b), start=1):
        if a < b:
            wins_a += 1
            who = name_a
        elif b < a:
            wins_b += 1
            who = name_b
        else:
            who = "Tie"
        print(f"  Lap {i}: {who} (gap {abs(a - b):.2f}s)")
    print(f"  Laps won: {name_a} {wins_a} - {wins_b} {name_b}")

    for name, laps in ((name_a, laps_a), (name_b, laps_b)):
        slow = unusually_slow_laps(laps)
        if slow:
            text = ", ".join(f"lap {n} ({t:.2f}s)" for n, t in slow)
            print(f"\nWARNING: unusually slow for {name}: {text}")

    print(f"\nGraph saved to: {graph_path}\n{line}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="F1 Lap Time Analyzer")
    parser.add_argument("--csv", help="path to a lap-time CSV file")
    parser.add_argument("--sample", action="store_true", help="use built-in sample data")
    parser.add_argument("--no-show", action="store_true", help="save the graph without opening a window")
    args = parser.parse_args()

    try:
        if args.csv:
            name_a, name_b, raw_a, raw_b = read_csv(args.csv)
        elif args.sample:
            name_a, name_b, raw_a, raw_b = "Driver A", "Driver B", SAMPLE_A, SAMPLE_B
        else:
            print("F1 Lap Time Analyzer\n  1) Sample data\n  2) Load lap_times.csv\n  3) Enter lap times manually")
            choice = input("Choose 1, 2 or 3: ").strip()
            if choice == "2":
                path = input("CSV path [lap_times.csv]: ").strip() or "lap_times.csv"
                name_a, name_b, raw_a, raw_b = read_csv(path)
            elif choice == "3":
                name_a, name_b, raw_a, raw_b = manual_input()
            else:
                name_a, name_b, raw_a, raw_b = "Driver A", "Driver B", SAMPLE_A, SAMPLE_B

        laps_a, laps_b = validate_pair(raw_a, raw_b, name_a, name_b)
    except FileNotFoundError as err:
        sys.exit(f"Error: file not found - {err.filename}")
    except ValueError as err:
        sys.exit(f"Error: {err}")

    plot_laps(laps_a, laps_b, name_a, name_b, show=not args.no_show)
    print_report(laps_a, laps_b, name_a, name_b, GRAPH_FILE)


if __name__ == "__main__":
    main()
