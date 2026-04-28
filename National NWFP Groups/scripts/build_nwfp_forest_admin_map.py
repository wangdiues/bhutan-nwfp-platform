from __future__ import annotations

import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parent.parent
DATA_PACKAGE = ROOT / "outputs" / "data" / "nwfp_management_groups_bhutan.gpkg"
TREE_FILE = ROOT / "National_NWFP_Groups_tree.txt"
META_FILE = ROOT / "National_NWFP_Groups.csv"
FOREST_ADMIN_BOUNDARY_FILE = ROOT / "Administrative Zones FR" / "Forest Administrative Boundary.shp"
OUTPUT_FIGURE_DIR = ROOT / "outputs" / "figures"
TARGET_CRS = 5266
SMALL_GROUP_THRESHOLD_HA = 25

BACKGROUND = "#faf8f4"
BOUNDARY_FILL = "#f4f0e7"
FOREST_LINE = "#575047"
NATIONAL_OUTLINE = "#7f776a"
TEXT_DARK = "#1f1a14"
TEXT_MID = "#665e53"
HAIRLINE = "#ddd5c8"
GROUP_FILL = "#9dcb60"
SMALL_SYMBOL_EDGE = "#fffdf8"
REFERENCE_LABEL_FILL = "#fffdf8"
REFERENCE_LABEL_LINE = "#b2a999"
OUTPUT_PNG_NAME = "bhutan_nwfp_management_groups_forest_admin_reference_600dpi.png"
OUTPUT_PDF_NAME = "bhutan_nwfp_management_groups_forest_admin_reference_vector.pdf"

AUTHORITY_BOUNDARY_MAP = {
    "Bumdelling Wildlife Sanctuary": "Bumdeling Wildlife Sanctuary",
    "DFO Bumthang": "Bumthang Forest Division",
    "DFO Dagana": "Dagana Forest Division",
    "DFO Gedu": "Chhukha Forest Division",
    "DFO Mongar": "Monggar Forest Division",
    "DFO Paro": "Paro Forest Division",
    "DFO Pemagatshel": "Pemagatshel Forest Division",
    "DFO Samchi": "Samtse Forest Division",
    "DFO Samdrup Jongkhar": "Samdrupjongkhar Forest Division",
    "DFO Sarpang": "Sarpang Forest Division",
    "DFO Trashigang": "Trashigang Forest Division",
    "DFO Tsirang": "Tsirang Forest Division",
    "DFO Zhemgang": "Zhemgang Forest Division",
    "Jigme Dorji National Park": "Jigme Dorji National Park",
    "Jigme Singye Wangchuck National Park": "Jigme Singye Wangchuck National Park",
    "Jomotshangkha Wildlife Sanctuary": "Jomotsangkha Wildlife Sanctuary",
    "Phrumsengla National Park": "Phrumsengla National Park",
    "Royal Manas National Park": "Royal Manas National Park",
    "Sakteng Wildlife Sanctuary": "Sakteng Wildlife Sanctuary",
    "Wangchuck Centennial National Park": "Wangchuck Centennial National Park",
}

BOUNDARY_NAME_FIXES = {
    "Jomotsangkha Wildlife Sanctuary": "Jomotshangkha Wildlife Sanctuary",
    "Samdrupjongkhar Forest Division": "Samdrup Jongkhar Forest Division",
}

LABEL_BIAS = {
    "Bumdeling Wildlife Sanctuary": (0.016, 0.020),
    "Bumthang Forest Division": (-0.014, 0.010),
    "Chhukha Forest Division": (-0.014, -0.020),
    "Dagana Forest Division": (-0.004, -0.026),
    "Jigme Dorji National Park": (-0.018, 0.016),
    "Jigme Singye Wangchuck National Park": (0.000, 0.014),
    "Jomotsangkha Wildlife Sanctuary": (0.028, -0.032),
    "Monggar Forest Division": (0.014, 0.006),
    "Paro Forest Division": (-0.020, 0.004),
    "Pemagatshel Forest Division": (-0.004, -0.022),
    "Phrumsengla National Park": (0.020, 0.018),
    "Royal Manas National Park": (0.004, -0.038),
    "Sakteng Wildlife Sanctuary": (0.048, 0.010),
    "Samdrupjongkhar Forest Division": (0.022, -0.008),
    "Samtse Forest Division": (-0.010, -0.008),
    "Sarpang Forest Division": (0.004, -0.030),
    "Trashigang Forest Division": (0.018, 0.006),
    "Tsirang Forest Division": (0.000, -0.020),
    "Wangchuck Centennial National Park": (0.000, 0.022),
    "Zhemgang Forest Division": (0.010, -0.010),
}


def load_groups() -> gpd.GeoDataFrame:
    if DATA_PACKAGE.exists():
        return gpd.read_file(DATA_PACKAGE, layer="nwfp_groups")

    from build_nwfp_bhutan_map import load_group_layers, load_metadata, parse_tree_inventory

    inventory = parse_tree_inventory(TREE_FILE)
    metadata = load_metadata(META_FILE)
    groups, _ = load_group_layers(inventory, metadata)
    return groups


def load_forest_admin() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(FOREST_ADMIN_BOUNDARY_FILE)
    return gdf.to_crs(TARGET_CRS)


def split_symbol_layers(groups: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    groups = groups.copy()
    groups["is_small_symbol"] = groups["map_area_ha"] < SMALL_GROUP_THRESHOLD_HA
    polygons = groups[~groups["is_small_symbol"]].copy()
    points = groups[groups["is_small_symbol"]].copy()
    if not points.empty:
        points["geometry"] = points.geometry.representative_point()
    return polygons, points


def build_metrics_line(groups: gpd.GeoDataFrame) -> str:
    mapped_count = len(groups)
    unit_count = groups["parent_unit"].nunique()
    total_area_ha = int(round(groups["map_area_ha"].sum()))
    median_area_ha = int(round(groups["map_area_ha"].median()))
    return (
        f"{mapped_count} mapped groups  |  "
        f"{unit_count} managing units  |  "
        f"{total_area_ha:,} ha total mapped area  |  "
        f"median group size {median_area_ha} ha"
    )


def clean_boundary_name(name: str) -> str:
    return BOUNDARY_NAME_FIXES.get(name, name)


def wrap_boundary_label(name: str) -> str:
    name = clean_boundary_name(name)
    suffix_map = {
        "Forest Division": ["Forest", "Division"],
        "National Park": ["National", "Park"],
        "Wildlife Sanctuary": ["Wildlife", "Sanctuary"],
        "Strict Nature Reserve": ["Strict Nature", "Reserve"],
    }
    for suffix, suffix_lines in suffix_map.items():
        if name.endswith(suffix):
            prefix = name[: -len(suffix)].strip()
            prefix_lines = textwrap.wrap(prefix, width=18) or [prefix]
            return "\n".join(prefix_lines + suffix_lines)
    return "\n".join(textwrap.wrap(name, width=18))


def build_authorities(forest_admin: gpd.GeoDataFrame, groups: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    summary = groups.copy()
    summary["boundary_name"] = summary["parent_unit"].map(AUTHORITY_BOUNDARY_MAP)

    unmatched = sorted(summary.loc[summary["boundary_name"].isna(), "parent_unit"].unique().tolist())
    if unmatched:
        raise ValueError(f"Unmapped managing units: {', '.join(unmatched)}")

    summary = (
        summary.groupby("boundary_name", dropna=False)
        .agg(group_count=("group_name", "size"), mapped_area_ha=("map_area_ha", "sum"))
        .reset_index()
    )

    authorities = forest_admin.copy()
    authorities["boundary_name"] = authorities["Name"].astype(str)
    authorities = authorities.merge(summary, how="left", on="boundary_name")
    authorities["group_count"] = authorities["group_count"].fillna(0).astype(int)
    authorities["mapped_area_ha"] = authorities["mapped_area_ha"].fillna(0.0)
    authorities["has_nwfp"] = authorities["group_count"] > 0
    rep = authorities.geometry.representative_point()
    authorities["anchor_x"] = rep.x
    authorities["anchor_y"] = rep.y
    authorities["label"] = authorities["boundary_name"].map(wrap_boundary_label)
    return authorities


def resolve_label_positions(authorities: gpd.GeoDataFrame) -> pd.DataFrame:
    labels = authorities[authorities["has_nwfp"]].copy()
    labels = labels.sort_values(["group_count", "mapped_area_ha"], ascending=[False, False]).reset_index(drop=True)

    xmin, ymin, xmax, ymax = authorities.total_bounds
    width = xmax - xmin
    height = ymax - ymin
    center_x = xmin + width / 2
    center_y = ymin + height / 2

    anchor_x = labels["anchor_x"].to_numpy(dtype=float)
    anchor_y = labels["anchor_y"].to_numpy(dtype=float)
    sign_x = np.where(anchor_x >= center_x, 1.0, -1.0)
    sign_y = np.where(anchor_y >= center_y, 1.0, -1.0)

    bias_x = np.array([LABEL_BIAS.get(name, (0.0, 0.0))[0] for name in labels["boundary_name"]])
    bias_y = np.array([LABEL_BIAS.get(name, (0.0, 0.0))[1] for name in labels["boundary_name"]])

    preferred_x = anchor_x + sign_x * width * 0.020 + bias_x * width
    preferred_y = anchor_y + sign_y * height * 0.018 + bias_y * height

    char_width = width * 0.0035
    line_height = height * 0.0145
    padding_x = width * 0.010
    padding_y = height * 0.010
    box_width = np.array(
        [max(len(line) for line in str(label).splitlines()) * char_width + padding_x for label in labels["label"]]
    )
    box_height = np.array([len(str(label).splitlines()) * line_height + padding_y for label in labels["label"]])

    label_x = preferred_x.copy()
    label_y = preferred_y.copy()
    margin_x = width * 0.020
    margin_y = height * 0.022

    for _ in range(280):
        moved = False
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                dx = label_x[j] - label_x[i]
                dy = label_y[j] - label_y[i]
                overlap_x = (box_width[i] + box_width[j]) / 2 - abs(dx)
                overlap_y = (box_height[i] + box_height[j]) / 2 - abs(dy)

                if overlap_x <= 0 or overlap_y <= 0:
                    continue

                moved = True
                if overlap_x < overlap_y:
                    shift = overlap_x / 2 + width * 0.0012
                    direction = 1.0 if dx >= 0 else -1.0
                    label_x[i] -= shift * direction
                    label_x[j] += shift * direction
                else:
                    shift = overlap_y / 2 + height * 0.0015
                    direction = 1.0 if dy >= 0 else -1.0
                    label_y[i] -= shift * direction
                    label_y[j] += shift * direction

        label_x += (preferred_x - label_x) * 0.08
        label_y += (preferred_y - label_y) * 0.08
        label_x = np.clip(label_x, xmin + margin_x + box_width / 2, xmax - margin_x - box_width / 2)
        label_y = np.clip(label_y, ymin + margin_y + box_height / 2, ymax - margin_y - box_height / 2)

        if not moved:
            break

    labels["label_x"] = label_x
    labels["label_y"] = label_y
    labels["box_width"] = box_width
    labels["box_height"] = box_height
    return pd.DataFrame(labels)


def draw_reference_labels(ax, labels: pd.DataFrame) -> None:
    for row in labels.itertuples(index=False):
        distance = float(np.hypot(row.label_x - row.anchor_x, row.label_y - row.anchor_y))
        if distance > min(row.box_width, row.box_height) * 0.35:
            ax.plot(
                [row.anchor_x, row.label_x],
                [row.anchor_y, row.label_y],
                color=REFERENCE_LABEL_LINE,
                linewidth=0.55,
                alpha=0.95,
                zorder=5,
            )

        ax.text(
            row.label_x,
            row.label_y,
            row.label,
            ha="center",
            va="center",
            fontsize=7.1,
            color=TEXT_DARK,
            linespacing=0.98,
            bbox={"boxstyle": "round,pad=0.20", "facecolor": REFERENCE_LABEL_FILL, "edgecolor": "none", "alpha": 0.97},
            path_effects=[pe.withStroke(linewidth=2.8, foreground=REFERENCE_LABEL_FILL)],
            zorder=6,
        )


def draw_legend(ax, labeled_authorities: int, total_authorities: int) -> None:
    ax.axis("off")

    ax.add_patch(
        Rectangle(
            (0.0, 0.56),
            0.05,
            0.05,
            transform=ax.transAxes,
            facecolor=GROUP_FILL,
            edgecolor=SMALL_SYMBOL_EDGE,
            linewidth=1.2,
        )
    )
    ax.text(0.065, 0.585, "NWFP management groups", transform=ax.transAxes, fontsize=10.4, color=TEXT_DARK, ha="left", va="center")

    ax.plot([0.0, 0.05], [0.33, 0.33], transform=ax.transAxes, color=FOREST_LINE, linewidth=1.25, solid_capstyle="round")
    ax.text(0.065, 0.33, "Forest administrative boundary", transform=ax.transAxes, fontsize=10.4, color=TEXT_DARK, ha="left", va="center")

    ax.scatter([0.025], [0.10], transform=ax.transAxes, s=38, c=GROUP_FILL, edgecolors=SMALL_SYMBOL_EDGE, linewidths=0.8, zorder=3)
    ax.text(0.065, 0.10, f"Groups under {SMALL_GROUP_THRESHOLD_HA} ha shown as points", transform=ax.transAxes, fontsize=9.4, color=TEXT_MID, ha="left", va="center")

    ax.text(0.64, 0.585, f"{labeled_authorities} of {total_authorities} authorities contain mapped groups", transform=ax.transAxes, fontsize=9.2, color=TEXT_MID, ha="left", va="center")
    ax.text(0.64, 0.33, "Only authorities with mapped groups are labeled", transform=ax.transAxes, fontsize=9.2, color=TEXT_MID, ha="left", va="center")


def draw_scale_bar(ax) -> None:
    ax.axis("off")
    x0, y0 = 0.07, 0.30
    total_width = 0.75
    segment_width = total_width / 2
    height = 0.15

    for idx, facecolor in enumerate((TEXT_DARK, BACKGROUND)):
        ax.add_patch(
            Rectangle(
                (x0 + idx * segment_width, y0),
                segment_width,
                height,
                transform=ax.transAxes,
                facecolor=facecolor,
                edgecolor=TEXT_DARK,
                linewidth=1.0,
            )
        )

    for idx, label in enumerate(("0", "25", "50 km")):
        ax.text(x0 + idx * segment_width, y0 - 0.10, label, transform=ax.transAxes, fontsize=9.4, color=TEXT_MID, ha="center", va="top", fontweight="semibold")


def draw_north_arrow(ax) -> None:
    ax.axis("off")
    ax.text(0.5, 0.99, "N", transform=ax.transAxes, fontsize=13.0, fontweight="bold", color=TEXT_DARK, ha="center", va="top")
    ax.annotate(
        "",
        xy=(0.5, 0.78),
        xytext=(0.5, 0.15),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops={"arrowstyle": "-|>", "lw": 2.0, "color": TEXT_DARK, "shrinkA": 0, "shrinkB": 0},
    )


def build_map(groups: gpd.GeoDataFrame, forest_admin: gpd.GeoDataFrame) -> list[Path]:
    OUTPUT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42
    plt.rcParams["font.family"] = "DejaVu Sans"

    authorities = build_authorities(forest_admin, groups)
    labels = resolve_label_positions(authorities)
    polygons, points = split_symbol_layers(groups)
    national_outline = forest_admin.dissolve(as_index=False)

    figure = plt.figure(figsize=(16.0, 10.0), facecolor=BACKGROUND)
    ax_map = figure.add_axes([0.04, 0.14, 0.90, 0.73])
    ax_legend = figure.add_axes([0.04, 0.03, 0.50, 0.09])
    ax_scale = figure.add_axes([0.76, 0.03, 0.16, 0.09])
    ax_arrow = figure.add_axes([0.925, 0.79, 0.05, 0.12])

    ax_map.set_facecolor(BACKGROUND)
    authorities.plot(ax=ax_map, facecolor=BOUNDARY_FILL, edgecolor="none", linewidth=0, zorder=1)

    if not polygons.empty:
        polygons.plot(ax=ax_map, color=GROUP_FILL, edgecolor=SMALL_SYMBOL_EDGE, linewidth=0.28, alpha=0.96, zorder=2)

    if not points.empty:
        ax_map.scatter(points.geometry.x, points.geometry.y, s=33, c=GROUP_FILL, edgecolors=SMALL_SYMBOL_EDGE, linewidths=0.75, zorder=3)

    authorities.boundary.plot(ax=ax_map, color=FOREST_LINE, linewidth=0.58, alpha=0.95, zorder=4)
    national_outline.boundary.plot(ax=ax_map, color=NATIONAL_OUTLINE, linewidth=1.10, zorder=5)
    draw_reference_labels(ax_map, labels)

    xmin, ymin, xmax, ymax = authorities.total_bounds
    x_pad = (xmax - xmin) * 0.035
    y_pad = (ymax - ymin) * 0.055
    ax_map.set_xlim(xmin - x_pad, xmax + x_pad)
    ax_map.set_ylim(ymin - y_pad, ymax + y_pad)
    ax_map.set_anchor("N")
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    for spine in ax_map.spines.values():
        spine.set_visible(False)

    metrics_line = build_metrics_line(groups)

    figure.text(0.04, 0.96, "NWFP Management Groups in Bhutan", ha="left", va="top", fontsize=26, fontweight="bold", color=TEXT_DARK, fontfamily="Georgia")
    figure.text(0.04, 0.925, "Reference map by forest administrative boundary", ha="left", va="top", fontsize=11.6, color=TEXT_MID)
    figure.text(0.04, 0.903, metrics_line, ha="left", va="top", fontsize=11.2, color=TEXT_DARK)
    figure.add_artist(Line2D([0.04, 0.96], [0.885, 0.885], transform=figure.transFigure, color=HAIRLINE, linewidth=1.2))

    draw_legend(ax_legend, int(authorities["has_nwfp"].sum()), len(authorities))
    draw_scale_bar(ax_scale)
    draw_north_arrow(ax_arrow)

    figure.text(0.04, 0.015, "Source layers in repository: NWFP group shapefiles and Forest Administrative Boundary. CRS: EPSG:5266 (Bhutan National Grid).", fontsize=9.0, color=TEXT_MID, style="italic")

    png_path = OUTPUT_FIGURE_DIR / OUTPUT_PNG_NAME
    pdf_path = OUTPUT_FIGURE_DIR / OUTPUT_PDF_NAME
    figure.savefig(png_path, dpi=600, facecolor=figure.get_facecolor(), bbox_inches="tight")
    figure.savefig(pdf_path, facecolor=figure.get_facecolor(), bbox_inches="tight")
    plt.close(figure)
    return [png_path, pdf_path]


def main() -> None:
    groups = load_groups()
    forest_admin = load_forest_admin()
    map_paths = build_map(groups, forest_admin)

    print(f"Mapped {len(groups)} groups from the data package.")
    for map_path in map_paths:
        print(f"Saved map: {map_path}")


if __name__ == "__main__":
    main()
