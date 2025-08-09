#!/usr/bin/env python3
import argparse
from fitparse import FitFile
from fitparse.utils import FitEOFError
import matplotlib.pyplot as plt
import itertools

def extract_distance_elevation(file_path):
    fitfile = FitFile(file_path, check_crc=False)
    distances = []
    elevations = []

    try:
        # Loop over every message in the file
        for msg in fitfile.get_messages():
            field_names = [f.name for f in msg.fields]

            # Only consider messages with both distance and altitude fields
            if "distance" in field_names and "altitude" in field_names:
                dist = msg.get_value("distance")
                alt = msg.get_value("altitude")
                if dist is not None and alt is not None:
                    distances.append(dist)
                    elevations.append(alt)

    except FitEOFError:
        print(f"Warning: Truncated FIT file {file_path}, data may be incomplete.")
    return distances, elevations

def plot_multiple(files):
    m_per_mi = 1609.344
    m_per_ft = 0.3048 
    all_norm_elev = []
    all_distances = []

    # Read all files first
    for f in files:
        d, e = extract_distance_elevation(f)
        if not e:  # Skip empty datasets
            print(f"Skipping {f} — no elevation data found.")
            continue

        # Convert to Imperial
        d = [x / m_per_mi for x in d]
        e = [x / m_per_ft for x in e]

        # offset for alignment to starting elevation
        offset = e[0]
        norm_e = [val - offset for val in e]
        all_distances.append(d)
        all_norm_elev.append(norm_e)

    # Determine shared y-scale
    chart_margin = 10
    max_range = max(max(e) for e in all_norm_elev)
    min_range = min(min(e) for e in all_norm_elev)
    y_top = max_range + chart_margin
    y_bot = min_range - chart_margin
    x_end = max(max(d) for d in all_distances)
    x_start = min(min(d) for d in all_distances)

    # Plot
    fig, ax = plt.subplots(figsize=(15, 7))
    colors = itertools.cycle(plt.cm.tab10.colors)

    for f, d, e in zip(files, all_distances, all_norm_elev):
        c = next(colors)
        ax.plot(d, e, color=c, lw=0.75, label=f)
        ax.fill_between(d, e, y_bot, color=c, alpha=0.2)
    ax.set_xlabel("Distance (mi)")
    ax.set_ylabel("Elevation Difference from Start (ft)")
    ax.set_xlim(x_start, x_end)
    ax.set_ylim(y_bot, y_top)
    ax.grid(True, which='both', linestyle='--', alpha=0.5)
    ax.legend(loc='upper right')
    plt.title("Elevation Comparison")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare elevation from multiple FIT files")
    parser.add_argument("files", nargs='+', help="FIT file paths (2 or more)")
    args = parser.parse_args()
    if len(args.files) < 2:
        raise ValueError("Please provide at least two FIT files.")
    plot_multiple(args.files)
