from __future__ import annotations

import re
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy import ndimage
from shapely import force_2d, union_all


ROOT = Path(__file__).resolve().parent.parent
TREE_FILE = ROOT / "National_NWFP_Groups_tree.txt"
META_FILE = ROOT / "National_NWFP_Groups.csv"
BOUNDARY_FILE = ROOT / "Dzongkhag Boundary" / "Dzongkhag Boundary.shp"
OUTPUT_DATA_DIR = ROOT / "outputs" / "data"
OUTPUT_FIGURE_DIR = ROOT / "outputs" / "figures"
TARGET_CRS = 5266

TREE_PATTERN = re.compile(r"^(?P<prefix>(?:\|   |    )*)(?:\+---|\\---)(?P<name>.+)$")

TYPE_ORDER = ("DFO", "PA")
TYPE_COLORS = {
    "DFO": "#1a9c7a",
    "PA": "#3a7fc7",
}
UNIT_TYPE_DISPLAY = {
    "DFO": "NWFP Groups in Divisions",
    "PA": "NWFP Groups in PAs",
}

BACKGROUND = "#faf8f5"
BOUNDARY_FILL = "#f5f2eb"
DZONGKHAG_LINE = "#d4cdc4"
NATIONAL_OUTLINE = "#8b8578"
TEXT_DARK = "#1a1a1a"
TEXT_MID = "#5a5a5a"
HAIRLINE = "#e0dcd5"
SMALL_SYMBOL_EDGE = "#ffffff"
SMALL_GROUP_THRESHOLD_HA = 25
HILLSHADE_ALPHA = 0.12
PUBLICATION_PNG_NAME = "bhutan_nwfp_management_groups_publication_600dpi.png"
PUBLICATION_PDF_NAME = "bhutan_nwfp_management_groups_publication_vector.pdf"


def normalize_name(value: str) -> str:
    text = str(value).lower()
    text = text.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", text)


def classify_unit_type(unit_name: str) -> str:
    if unit_name.startswith("DFO "):
        return "DFO"
    if unit_name.endswith("National Park") or unit_name.endswith("Wildlife Sanctuary"):
        return "PA"
    return "Other"


def parse_tree_inventory(tree_file: Path) -> pd.DataFrame:
    stack: dict[int, str] = {}
    rows: list[dict[str, object]] = []

    for line in tree_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = TREE_PATTERN.match(line)
        if not match:
            continue

        depth = len(match.group("prefix")) // 4
        name = match.group("name").strip()
        stack[depth] = name
        for key in list(stack):
            if key > depth:
                del stack[key]

        if depth != 1:
            continue

        parent_unit = stack.get(0)
        if not parent_unit or parent_unit == "Dzongkhag Boundary":
            continue

        folder = ROOT / parent_unit / name
        preferred = folder / f"{name}.shp"
        shp_path = preferred if preferred.exists() else next(folder.glob("*.shp"), None)

        rows.append(
            {
                "parent_unit": parent_unit,
                "unit_type": classify_unit_type(parent_unit),
                "group_name": name,
                "folder_path": str(folder),
                "shp_path": str(shp_path) if shp_path else None,
                "has_shapefile": shp_path is not None,
                "tree_key": normalize_name(name),
            }
        )

    return pd.DataFrame(rows)


def load_metadata(meta_file: Path) -> pd.DataFrame:
    metadata = pd.read_csv(meta_file)
    metadata["meta_key"] = metadata["Group Name"].map(normalize_name)
    return metadata


def select_metadata_row(
    group_name: str,
    tree_key: str,
    metadata_by_key: dict[str, pd.DataFrame],
) -> pd.Series | None:
    if tree_key in metadata_by_key:
        return metadata_by_key[tree_key].iloc[0]

    aliases = {
        normalize_name("Jabgang Cane (Plectocomia himalayana) NWFP group"): normalize_name("Jabgang NWFP group"),
    }
    if tree_key in aliases and aliases[tree_key] in metadata_by_key:
        return metadata_by_key[aliases[tree_key]].iloc[0]

    return None


def keep_polygonal(geometry):
    if geometry is None or geometry.is_empty:
        return None
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        return geometry
    if hasattr(geometry, "geoms"):
        parts = [part for part in geometry.geoms if part.geom_type in {"Polygon", "MultiPolygon"}]
        if not parts:
            return None
        return union_all(parts)
    return None


def clean_geometry_frame(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    frame = frame.copy()
    frame["geometry"] = frame.geometry.make_valid()
    frame["geometry"] = frame.geometry.map(force_2d)
    frame["geometry"] = frame.geometry.map(keep_polygonal)
    frame = frame[frame["geometry"].notna()].copy()
    frame = frame[~frame.geometry.is_empty].copy()
    return frame


def load_boundary_layer() -> gpd.GeoDataFrame:
    boundary = gpd.read_file(BOUNDARY_FILE)
    boundary = clean_geometry_frame(boundary)
    return boundary.to_crs(TARGET_CRS)


def create_hillshade_data(boundary: gpd.GeoDataFrame, resolution: int = 500) -> np.ndarray:
    """Generate synthetic hillshade terrain for visual depth."""
    xmin, ymin, xmax, ymax = boundary.total_bounds
    x = np.linspace(xmin, xmax, resolution)
    y = np.linspace(ymin, ymax, resolution)
    xx, yy = np.meshgrid(x, y)
    
    np.random.seed(42)
    base = np.random.rand(resolution, resolution) * 0.3
    from scipy.ndimage import gaussian_filter
    base = gaussian_filter(base, sigma=15)
    
    gradient_x = np.gradient(base, axis=1)
    gradient_y = np.gradient(base, axis=0)
    azimuth = 315 * np.pi / 180
    altitude = 45 * np.pi / 180
    hillshade = (
        np.sin(altitude) * np.ones_like(base) +
        np.cos(altitude) * np.sin(azimuth) * gradient_x +
        np.cos(altitude) * np.cos(azimuth) * gradient_y
    )
    hillshade = (hillshade - hillshade.min()) / (hillshade.max() - hillshade.min())
    return hillshade


def load_group_layers(
    inventory: pd.DataFrame,
    metadata: pd.DataFrame,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    metadata_by_key = {key: group for key, group in metadata.groupby("meta_key", dropna=False)}
    records: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []

    for row in inventory.itertuples(index=False):
        if not row.has_shapefile or not row.shp_path:
            missing.append(
                {
                    "parent_unit": row.parent_unit,
                    "group_name": row.group_name,
                    "reason": "Listed in tree file but no shapefile was found in the folder.",
                }
            )
            continue

        layer = gpd.read_file(row.shp_path)
        original_feature_count = len(layer)
        source_crs = layer.crs.to_string() if layer.crs else None

        layer = clean_geometry_frame(layer)
        if layer.empty:
            missing.append(
                {
                    "parent_unit": row.parent_unit,
                    "group_name": row.group_name,
                    "reason": "Shapefile loaded, but no polygonal geometry remained after repair.",
                }
            )
            continue

        repaired_feature_count = len(layer)
        layer = layer.to_crs(TARGET_CRS)
        merged_geometry = keep_polygonal(union_all(layer.geometry.tolist()))
        if merged_geometry is None or merged_geometry.is_empty:
            missing.append(
                {
                    "parent_unit": row.parent_unit,
                    "group_name": row.group_name,
                    "reason": "Geometry repair succeeded, but the dissolved result was empty.",
                }
            )
            continue

        metadata_row = select_metadata_row(row.group_name, row.tree_key, metadata_by_key)
        metadata_dict = metadata_row.to_dict() if metadata_row is not None else {}

        records.append(
            {
                "parent_unit": row.parent_unit,
                "unit_type": row.unit_type,
                "group_name": row.group_name,
                "tree_key": row.tree_key,
                "source_path": row.shp_path,
                "source_crs": source_crs,
                "source_feature_count": original_feature_count,
                "repaired_feature_count": repaired_feature_count,
                "metadata_match": bool(metadata_dict),
                "meta_group_name": metadata_dict.get("Group Name"),
                "meta_dzongkhag": metadata_dict.get("Dzongkhag"),
                "meta_division_park": metadata_dict.get("Division/Park"),
                "meta_gewog": metadata_dict.get("Gewog"),
                "meta_village": metadata_dict.get("Village"),
                "meta_members_nos": metadata_dict.get("Members (Nos)"),
                "meta_female_nos": metadata_dict.get("Female (Nos)"),
                "meta_area_ha": metadata_dict.get("Area (ha)"),
                "meta_estd_year": metadata_dict.get("Estd year"),
                "meta_revision_year": metadata_dict.get("Revision Year"),
                "meta_plan_period": metadata_dict.get("Plan Period"),
                "meta_plan_type": metadata_dict.get("Plan Type"),
                "meta_contact_details": metadata_dict.get("Contact Details"),
                "meta_species": metadata_dict.get("Species"),
                "geometry": merged_geometry,
            }
        )

    groups = gpd.GeoDataFrame(records, geometry="geometry", crs=f"EPSG:{TARGET_CRS}")
    groups["map_area_ha"] = groups.geometry.area / 10000.0
    groups["representative_x"] = groups.geometry.representative_point().x
    groups["representative_y"] = groups.geometry.representative_point().y
    return groups, pd.DataFrame(missing)


def draw_legend(ax, unit_type_counts: pd.Series) -> None:
    ax.axis("off")

    y_positions = [0.55, 0.25]
    for y, unit_type in zip(y_positions, TYPE_ORDER, strict=True):
        ax.add_patch(
            Rectangle(
                (0.0, y - 0.05),
                0.05,
                0.05,
                transform=ax.transAxes,
                facecolor=TYPE_COLORS[unit_type],
                edgecolor='#ffffff',
                linewidth=1.2,
            )
        )
        ax.text(
            0.065,
            y - 0.025,
            f"{UNIT_TYPE_DISPLAY[unit_type]} ({int(unit_type_counts[unit_type])})",
            transform=ax.transAxes,
            fontsize=10.5,
            color=TEXT_DARK,
            ha="left",
            va="center",
        )

    ax.scatter(
        [0.025],
        [0.03],
        transform=ax.transAxes,
        s=38,
        c="#857f73",
        edgecolors='#ffffff',
        linewidths=0.8,
        zorder=3,
    )
    ax.text(
        0.065,
        0.03,
        f"Groups under {SMALL_GROUP_THRESHOLD_HA} ha shown as points",
        transform=ax.transAxes,
        fontsize=9.5,
        color=TEXT_MID,
        ha="left",
        va="center",
    )


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
        ax.text(
            x0 + idx * segment_width,
            y0 - 0.10,
            label,
            transform=ax.transAxes,
            fontsize=9.5,
            color=TEXT_MID,
            ha="center",
            va="top",
            fontweight='semibold',
        )


def draw_north_arrow(ax) -> None:
    ax.axis("off")
    ax.text(
        0.5,
        0.99,
        "N",
        transform=ax.transAxes,
        fontsize=13.0,
        fontweight="bold",
        color=TEXT_DARK,
        ha="center",
        va="top",
    )
    ax.annotate(
        "",
        xy=(0.5, 0.78),
        xytext=(0.5, 0.15),
        xycoords=ax.transAxes,
        textcoords=ax.transAxes,
        arrowprops={"arrowstyle": "-|>", "lw": 2.0, "color": TEXT_DARK, "shrinkA": 0, "shrinkB": 0},
    )


def draw_publication_map(
    groups: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame,
    inventory: pd.DataFrame,
    missing: pd.DataFrame,
) -> list[Path]:
    OUTPUT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["ps.fonttype"] = 42

    plt.rcParams["font.family"] = "DejaVu Sans"

    figure = plt.figure(figsize=(16.0, 10.0), facecolor=BACKGROUND)
    ax_map = figure.add_axes([0.04, 0.15, 0.88, 0.70])
    ax_legend = figure.add_axes([0.04, 0.03, 0.36, 0.095])
    ax_scale = figure.add_axes([0.74, 0.03, 0.18, 0.095])
    ax_arrow = figure.add_axes([0.915, 0.79, 0.055, 0.12])

    ax_map.set_facecolor(BACKGROUND)
    
    hillshade = create_hillshade_data(boundary, resolution=600)
    xmin, ymin, xmax, ymax = boundary.total_bounds
    ax_map.imshow(
        hillshade,
        cmap='binary_r',
        alpha=HILLSHADE_ALPHA,
        extent=(xmin, xmax, ymin, ymax),
        zorder=0,
        interpolation='bilinear',
    )
    
    boundary.plot(ax=ax_map, facecolor=BOUNDARY_FILL, edgecolor="none", linewidth=0, zorder=1)

    groups = groups.copy()
    groups["is_small_symbol"] = groups["map_area_ha"] < SMALL_GROUP_THRESHOLD_HA
    national_outline = boundary.dissolve(as_index=False)

    for unit_type in TYPE_ORDER:
        color = TYPE_COLORS[unit_type]
        subset = groups[groups["unit_type"] == unit_type]
        if subset.empty:
            continue
        polygon_subset = subset[~subset["is_small_symbol"]]
        point_subset = subset[subset["is_small_symbol"]]

        if not polygon_subset.empty:
            polygon_subset.plot(
                ax=ax_map,
                color=color,
                edgecolor=SMALL_SYMBOL_EDGE,
                linewidth=0.35,
                alpha=0.92,
                zorder=2,
            )
            polygon_subset.boundary.plot(
                ax=ax_map,
                color='#ffffff',
                linewidth=0.5,
                alpha=0.4,
                zorder=3,
            )

        if not point_subset.empty:
            points = point_subset.geometry.representative_point()
            ax_map.scatter(
                points.x,
                points.y,
                s=35,
                c=color,
                edgecolors=SMALL_SYMBOL_EDGE,
                linewidths=0.8,
                zorder=3,
            )

    boundary.boundary.plot(ax=ax_map, color=DZONGKHAG_LINE, linewidth=0.55, zorder=4)
    national_outline.boundary.plot(ax=ax_map, color=NATIONAL_OUTLINE, linewidth=1.1, zorder=5)

    xmin, ymin, xmax, ymax = boundary.total_bounds
    x_pad = (xmax - xmin) * 0.03
    y_pad = (ymax - ymin) * 0.04
    ax_map.set_xlim(xmin - x_pad, xmax + x_pad)
    ax_map.set_ylim(ymin - y_pad, ymax + y_pad)
    ax_map.set_anchor("N")
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    for spine in ax_map.spines.values():
        spine.set_visible(False)

    unit_type_counts = groups["unit_type"].value_counts().reindex(TYPE_ORDER, fill_value=0)

    mapped_count = len(groups)
    unit_count = groups["parent_unit"].nunique()
    total_area_ha = int(round(groups["map_area_ha"].sum()))
    median_area_ha = int(round(groups["map_area_ha"].median()))
    metrics_line = (
        f"{mapped_count} mapped groups  |  "
        f"{unit_count} managing units  |  "
        f"{total_area_ha:,} ha total mapped area  |  "
        f"median group size {median_area_ha} ha"
    )

    figure.text(
        0.04,
        0.96,
        "NWFP Management Groups of Bhutan",
        ha="left",
        va="top",
        fontsize=26,
        fontweight="bold",
        color=TEXT_DARK,
    )
    figure.text(
        0.04,
        0.925,
        metrics_line,
        ha="left",
        va="top",
        fontsize=11.5,
        color=TEXT_DARK,
    )
    figure.add_artist(Line2D([0.04, 0.96], [0.90, 0.90], transform=figure.transFigure, color=HAIRLINE, linewidth=1.2))

    draw_legend(ax_legend, unit_type_counts)
    draw_scale_bar(ax_scale)
    draw_north_arrow(ax_arrow)

    figure.text(
        0.04,
        0.015,
        "Source layers in repository: NWFP group shapefiles and Dzongkhag Boundary. CRS: EPSG:5266 (Bhutan National Grid).",
        fontsize=9.0,
        color=TEXT_MID,
        style='italic',
    )

    png_path = OUTPUT_FIGURE_DIR / PUBLICATION_PNG_NAME
    pdf_path = OUTPUT_FIGURE_DIR / PUBLICATION_PDF_NAME
    figure.savefig(png_path, dpi=600, facecolor=figure.get_facecolor(), bbox_inches='tight')
    figure.savefig(pdf_path, facecolor=figure.get_facecolor(), bbox_inches='tight')
    plt.close(figure)
    return [png_path, pdf_path]


def export_outputs(
    inventory: pd.DataFrame,
    groups: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame,
    missing: pd.DataFrame,
) -> None:
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    inventory.to_csv(OUTPUT_DATA_DIR / "nwfp_tree_inventory.csv", index=False)
    if not missing.empty:
        missing.to_csv(OUTPUT_DATA_DIR / "nwfp_tree_missing_layers.csv", index=False)

    gpkg_path = OUTPUT_DATA_DIR / "nwfp_management_groups_bhutan.gpkg"
    groups.to_file(gpkg_path, layer="nwfp_groups", driver="GPKG")
    boundary.to_file(gpkg_path, layer="dzongkhag_boundary", driver="GPKG")


def main() -> None:
    inventory = parse_tree_inventory(TREE_FILE)
    metadata = load_metadata(META_FILE)
    boundary = load_boundary_layer()
    groups, missing = load_group_layers(inventory, metadata)
    export_outputs(inventory, groups, boundary, missing)
    map_paths = draw_publication_map(groups, boundary, inventory, missing)

    print(f"Parsed {len(inventory)} tree-listed groups.")
    print(f"Mapped {len(groups)} groups from shapefiles.")
    print(f"Missing or unmapped groups: {len(missing)}.")
    for map_path in map_paths:
        print(f"Saved map: {map_path}")
    print(f"Saved data package: {OUTPUT_DATA_DIR / 'nwfp_management_groups_bhutan.gpkg'}")


if __name__ == "__main__":
    main()
