required_packages <- c(
  "cowplot",
  "dplyr",
  "ggplot2",
  "readr",
  "scales",
  "sf",
  "stringr"
)

missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]

if (length(missing_packages)) {
  stop(
    sprintf(
      "Missing required packages: %s\nRun: Rscript scripts/install_nwfp_map_packages.R",
      paste(missing_packages, collapse = ", ")
    ),
    call. = FALSE
  )
}

suppressPackageStartupMessages({
  library(cowplot)
  library(dplyr)
  library(ggplot2)
  library(readr)
  library(scales)
  library(sf)
  library(stringr)
  library(grid)
})

get_script_path <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg)) {
    return(normalizePath(sub("^--file=", "", file_arg[[1]]), winslash = "/", mustWork = TRUE))
  }

  normalizePath(
    file.path(getwd(), "scripts", "build_nwfp_bhutan_map.R"),
    winslash = "/",
    mustWork = FALSE
  )
}

`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0 || all(is.na(x)) || !nzchar(as.character(x[[1]]))) {
    return(y)
  }
  x
}

SCRIPT_PATH <- get_script_path()
ROOT <- normalizePath(file.path(dirname(SCRIPT_PATH), ".."), winslash = "/", mustWork = TRUE)
TREE_FILE <- file.path(ROOT, "National_NWFP_Groups_tree.txt")
META_FILE <- file.path(ROOT, "National_NWFP_Groups.csv")
BOUNDARY_FILE <- file.path(ROOT, "Dzongkhag Boundary", "Dzongkhag Boundary.shp")
OUTPUT_DATA_DIR <- file.path(ROOT, "outputs", "data")
OUTPUT_FIGURE_DIR <- file.path(ROOT, "outputs", "figures")
TARGET_CRS <- 5266

TYPE_ORDER <- c("DFO", "National Park", "Wildlife Sanctuary")
TYPE_COLORS <- c(
  "DFO" = "#0f8f6d",
  "National Park" = "#2f78b7",
  "Wildlife Sanctuary" = "#d58a1f"
)
UNIT_TYPE_DISPLAY <- c(
  "DFO" = "Divisional Forest Office",
  "National Park" = "National Park",
  "Wildlife Sanctuary" = "Wildlife Sanctuary"
)

BACKGROUND <- "#f7f4ee"
BOUNDARY_FILL <- "#efe9dd"
DZONGKHAG_LINE <- "#c4bcad"
NATIONAL_OUTLINE <- "#8f8879"
TEXT_DARK <- "#1f2320"
TEXT_MID <- "#666055"
HAIRLINE <- "#d6cfbf"
SMALL_SYMBOL_EDGE <- "#fbf8f2"
SMALL_GROUP_THRESHOLD_HA <- 25
PUBLICATION_PNG_NAME <- "bhutan_nwfp_management_groups_publication_600dpi.png"
PUBLICATION_PDF_NAME <- "bhutan_nwfp_management_groups_publication_vector.pdf"

normalize_name <- function(value) {
  text <- tolower(as.character(value))
  text <- gsub("&", "and", text, fixed = TRUE)
  gsub("[^a-z0-9]+", "", text)
}

classify_unit_type <- function(unit_name) {
  if (startsWith(unit_name, "DFO ")) {
    return("DFO")
  }
  if (endsWith(unit_name, "National Park")) {
    return("National Park")
  }
  if (endsWith(unit_name, "Wildlife Sanctuary")) {
    return("Wildlife Sanctuary")
  }
  "Other"
}

parse_tree_inventory <- function(tree_file) {
  lines <- readLines(tree_file, warn = FALSE, encoding = "UTF-8")
  pattern <- "^((?:\\|   |    )*)(?:\\+---|\\\\---)(.+)$"
  stack <- list()
  rows <- list()

  for (line in lines) {
    matched <- str_match(line, pattern)
    if (is.na(matched[1, 1])) {
      next
    }

    prefix <- matched[1, 2]
    name <- trimws(matched[1, 3])
    depth <- nchar(prefix, type = "bytes") %/% 4L

    stack[[as.character(depth)]] <- name
    stack_depths <- suppressWarnings(as.integer(names(stack)))
    stack <- stack[stack_depths <= depth]

    if (depth != 1L) {
      next
    }

    parent_unit <- stack[["0"]]
    if (is.null(parent_unit) || identical(parent_unit, "Dzongkhag Boundary")) {
      next
    }

    folder <- file.path(ROOT, parent_unit, name)
    preferred <- file.path(folder, paste0(name, ".shp"))
    if (file.exists(preferred)) {
      shp_path <- preferred
    } else if (dir.exists(folder)) {
      candidates <- list.files(folder, pattern = "\\.shp$", full.names = TRUE, ignore.case = TRUE)
      shp_path <- if (length(candidates)) candidates[[1]] else NA_character_
    } else {
      shp_path <- NA_character_
    }

    rows[[length(rows) + 1L]] <- data.frame(
      parent_unit = parent_unit,
      unit_type = classify_unit_type(parent_unit),
      group_name = name,
      folder_path = folder,
      shp_path = shp_path,
      has_shapefile = !is.na(shp_path),
      tree_key = normalize_name(name),
      stringsAsFactors = FALSE
    )
  }

  bind_rows(rows)
}

load_metadata <- function(meta_file) {
  metadata <- read_csv(meta_file, show_col_types = FALSE)
  metadata$meta_key <- normalize_name(metadata$`Group Name`)
  metadata
}

safe_pull <- function(data, field_name) {
  if (!(field_name %in% names(data))) {
    return(NA)
  }
  data[[field_name]][1]
}

select_metadata_row <- function(tree_key, metadata_by_key) {
  aliases <- setNames(
    normalize_name("Jabgang NWFP group"),
    normalize_name("Jabgang Cane (Plectocomia himalayana) NWFP group")
  )

  if (!is.null(metadata_by_key[[tree_key]])) {
    return(metadata_by_key[[tree_key]][1, , drop = FALSE])
  }

  alias_key <- aliases[[tree_key]]
  if (!is.null(alias_key) && !is.null(metadata_by_key[[alias_key]])) {
    return(metadata_by_key[[alias_key]][1, , drop = FALSE])
  }

  NULL
}

extract_polygon_sfc <- function(geom, crs) {
  geom <- suppressWarnings(st_make_valid(geom))
  geom <- suppressWarnings(st_zm(geom, drop = TRUE, what = "ZM"))
  geom <- suppressWarnings(st_collection_extract(geom, "POLYGON"))
  geom <- geom[!st_is_empty(geom)]
  st_set_crs(geom, crs)
}

load_boundary_layer <- function() {
  boundary <- st_read(BOUNDARY_FILE, quiet = TRUE)
  boundary <- suppressWarnings(st_make_valid(boundary))
  boundary <- suppressWarnings(st_zm(boundary, drop = TRUE, what = "ZM"))
  boundary <- suppressWarnings(st_collection_extract(boundary, "POLYGON"))
  boundary <- boundary[!st_is_empty(boundary), ]
  st_transform(boundary, TARGET_CRS)
}

load_group_layers <- function(inventory, metadata) {
  metadata_by_key <- split(metadata, metadata$meta_key)
  records <- list()
  missing <- list()

  for (idx in seq_len(nrow(inventory))) {
    row <- inventory[idx, , drop = FALSE]

    if (!isTRUE(row$has_shapefile) || is.na(row$shp_path) || !file.exists(row$shp_path)) {
      missing[[length(missing) + 1L]] <- data.frame(
        parent_unit = row$parent_unit,
        group_name = row$group_name,
        reason = "Listed in tree file but no shapefile was found in the folder.",
        stringsAsFactors = FALSE
      )
      next
    }

    layer <- st_read(row$shp_path, quiet = TRUE)
    original_feature_count <- nrow(layer)
    layer_crs <- st_crs(layer)
    fallback_crs <- if (!is.na(layer_crs$epsg)) paste0("EPSG:", layer_crs$epsg) else NA_character_
    source_crs <- layer_crs$input %||% fallback_crs

    geom <- extract_polygon_sfc(st_geometry(layer), layer_crs)
    if (!length(geom)) {
      missing[[length(missing) + 1L]] <- data.frame(
        parent_unit = row$parent_unit,
        group_name = row$group_name,
        reason = "Shapefile loaded, but no polygonal geometry remained after repair.",
        stringsAsFactors = FALSE
      )
      next
    }

    repaired_feature_count <- length(geom)
    geom_sf <- st_sf(geometry = geom)
    geom_sf <- st_transform(geom_sf, TARGET_CRS)
    merged <- suppressWarnings(st_union(st_geometry(geom_sf)))
    merged <- extract_polygon_sfc(merged, TARGET_CRS)

    if (!length(merged)) {
      missing[[length(missing) + 1L]] <- data.frame(
        parent_unit = row$parent_unit,
        group_name = row$group_name,
        reason = "Geometry repair succeeded, but the dissolved result was empty.",
        stringsAsFactors = FALSE
      )
      next
    }

    merged_geometry <- suppressWarnings(st_union(merged))[[1]]
    metadata_row <- select_metadata_row(row$tree_key, metadata_by_key)

    records[[length(records) + 1L]] <- data.frame(
      parent_unit = row$parent_unit,
      unit_type = row$unit_type,
      group_name = row$group_name,
      tree_key = row$tree_key,
      source_path = row$shp_path,
      source_crs = source_crs,
      source_feature_count = original_feature_count,
      repaired_feature_count = repaired_feature_count,
      metadata_match = !is.null(metadata_row),
      meta_group_name = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Group Name"),
      meta_dzongkhag = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Dzongkhag"),
      meta_division_park = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Division/Park"),
      meta_gewog = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Gewog"),
      meta_village = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Village"),
      meta_members_nos = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Members (Nos)"),
      meta_female_nos = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Female (Nos)"),
      meta_area_ha = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Area (ha)"),
      meta_estd_year = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Estd year"),
      meta_revision_year = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Revision Year"),
      meta_plan_period = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Plan Period"),
      meta_plan_type = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Plan Type"),
      meta_contact_details = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Contact Details"),
      meta_species = if (is.null(metadata_row)) NA else safe_pull(metadata_row, "Species"),
      stringsAsFactors = FALSE
    )
    records[[length(records)]]$geometry <- list(merged_geometry)
  }

  if (!length(records)) {
    stop("No NWFP group geometries could be loaded.", call. = FALSE)
  }

  groups_df <- bind_rows(records)
  groups_df$geometry <- st_sfc(groups_df$geometry, crs = TARGET_CRS)
  groups <- st_as_sf(groups_df, sf_column_name = "geometry", crs = TARGET_CRS)
  groups$map_area_ha <- as.numeric(st_area(groups)) / 10000

  rep_points <- st_point_on_surface(groups)
  rep_coords <- st_coordinates(rep_points)
  groups$representative_x <- rep_coords[, 1]
  groups$representative_y <- rep_coords[, 2]

  missing_df <- if (length(missing)) bind_rows(missing) else data.frame()
  list(groups = groups, missing = missing_df)
}

build_legend_plot <- function(unit_type_counts) {
  legend_df <- data.frame(
    unit_type = factor(TYPE_ORDER, levels = TYPE_ORDER),
    label = paste0(UNIT_TYPE_DISPLAY[TYPE_ORDER], " (", as.integer(unit_type_counts[TYPE_ORDER]), ")"),
    y = c(0.70, 0.43, 0.16),
    stringsAsFactors = FALSE
  )

  ggplot() +
    annotate(
      "text",
      x = 0,
      y = 0.98,
      label = "Managing authority",
      hjust = 0,
      vjust = 1,
      family = "sans",
      fontface = "bold",
      size = 3.6,
      color = TEXT_DARK
    ) +
    geom_rect(
      data = legend_df,
      aes(
        xmin = 0,
        xmax = 0.035,
        ymin = y - 0.035,
        ymax = y,
        fill = unit_type
      ),
      show.legend = FALSE
    ) +
    geom_text(
      data = legend_df,
      aes(x = 0.05, y = y - 0.017, label = label),
      hjust = 0,
      vjust = 0.5,
      family = "sans",
      size = 3.2,
      color = TEXT_DARK
    ) +
    annotate(
      "point",
      x = 0.017,
      y = 0.04,
      shape = 21,
      size = 1.9,
      fill = "#857f73",
      color = SMALL_SYMBOL_EDGE,
      stroke = 0.35
    ) +
    annotate(
      "text",
      x = 0.05,
      y = 0.04,
      label = paste0("Groups under ", SMALL_GROUP_THRESHOLD_HA, " ha shown as points"),
      hjust = 0,
      vjust = 0.5,
      family = "sans",
      size = 2.9,
      color = TEXT_MID
    ) +
    scale_fill_manual(values = TYPE_COLORS) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE, clip = "off") +
    theme_void() +
    theme(plot.background = element_rect(fill = BACKGROUND, color = NA))
}

build_scale_plot <- function() {
  ggplot() +
    annotate(
      "text",
      x = 0,
      y = 0.98,
      label = "Scale",
      hjust = 0,
      vjust = 1,
      family = "sans",
      fontface = "bold",
      size = 3.6,
      color = TEXT_DARK
    ) +
    annotate(
      "rect",
      xmin = 0.07,
      xmax = 0.43,
      ymin = 0.38,
      ymax = 0.50,
      fill = TEXT_DARK,
      color = TEXT_DARK,
      linewidth = 0.25
    ) +
    annotate(
      "rect",
      xmin = 0.43,
      xmax = 0.79,
      ymin = 0.38,
      ymax = 0.50,
      fill = BACKGROUND,
      color = TEXT_DARK,
      linewidth = 0.25
    ) +
    annotate("text", x = 0.07, y = 0.27, label = "0", hjust = 0.5, vjust = 1, size = 2.8, color = TEXT_MID) +
    annotate("text", x = 0.43, y = 0.27, label = "25", hjust = 0.5, vjust = 1, size = 2.8, color = TEXT_MID) +
    annotate("text", x = 0.79, y = 0.27, label = "50 km", hjust = 0.5, vjust = 1, size = 2.8, color = TEXT_MID) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE, clip = "off") +
    theme_void() +
    theme(plot.background = element_rect(fill = BACKGROUND, color = NA))
}

build_arrow_plot <- function() {
  ggplot() +
    annotate(
      "text",
      x = 0.5,
      y = 0.99,
      label = "N",
      hjust = 0.5,
      vjust = 1,
      family = "sans",
      fontface = "bold",
      size = 4.0,
      color = TEXT_DARK
    ) +
    annotate(
      "segment",
      x = 0.5,
      xend = 0.5,
      y = 0.18,
      yend = 0.82,
      linewidth = 0.45,
      color = TEXT_DARK,
      arrow = arrow(length = unit(3.0, "mm"), type = "closed")
    ) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE, clip = "off") +
    theme_void() +
    theme(plot.background = element_rect(fill = BACKGROUND, color = NA))
}

compose_map_page <- function(groups, boundary) {
  groups$is_small_symbol <- groups$map_area_ha < SMALL_GROUP_THRESHOLD_HA
  polygon_groups <- groups[!groups$is_small_symbol, ]
  point_groups <- st_point_on_surface(groups[groups$is_small_symbol, , drop = FALSE])
  national_outline <- st_as_sf(
    data.frame(name = "Bhutan"),
    geometry = st_sfc(st_union(st_geometry(boundary)), crs = TARGET_CRS)
  )

  bbox <- st_bbox(boundary)
  x_pad <- (bbox[["xmax"]] - bbox[["xmin"]]) * 0.03
  y_pad <- (bbox[["ymax"]] - bbox[["ymin"]]) * 0.04
  unit_type_counts <- table(factor(groups$unit_type, levels = TYPE_ORDER))

  mapped_count <- nrow(groups)
  unit_count <- dplyr::n_distinct(groups$parent_unit)
  total_area_ha <- round(sum(groups$map_area_ha))
  median_area_ha <- round(median(groups$map_area_ha))
  metrics_line <- paste0(
    mapped_count, " mapped groups  |  ",
    unit_count, " managing units  |  ",
    comma(total_area_ha), " ha total mapped area  |  ",
    "median group size ", comma(median_area_ha), " ha"
  )

  map_plot <- ggplot() +
    geom_sf(data = boundary, fill = BOUNDARY_FILL, color = NA, linewidth = 0) +
    geom_sf(
      data = polygon_groups,
      aes(fill = factor(unit_type, levels = TYPE_ORDER)),
      color = SMALL_SYMBOL_EDGE,
      linewidth = 0.12,
      alpha = 0.96,
      show.legend = FALSE
    ) +
    geom_sf(
      data = point_groups,
      aes(fill = factor(unit_type, levels = TYPE_ORDER)),
      shape = 21,
      color = SMALL_SYMBOL_EDGE,
      stroke = 0.22,
      size = 1.45,
      show.legend = FALSE
    ) +
    geom_sf(data = boundary, fill = NA, color = DZONGKHAG_LINE, linewidth = 0.14, show.legend = FALSE) +
    geom_sf(data = national_outline, fill = NA, color = NATIONAL_OUTLINE, linewidth = 0.32, show.legend = FALSE) +
    scale_fill_manual(values = TYPE_COLORS) +
    coord_sf(
      xlim = c(bbox[["xmin"]] - x_pad, bbox[["xmax"]] + x_pad),
      ylim = c(bbox[["ymin"]] - y_pad, bbox[["ymax"]] + y_pad),
      expand = FALSE,
      clip = "off"
    ) +
    theme_void() +
    theme(
      plot.background = element_rect(fill = BACKGROUND, color = NA),
      panel.background = element_rect(fill = BACKGROUND, color = NA),
      plot.margin = margin(0, 0, 0, 0)
    )

  header_rule <- segmentsGrob(
    x0 = unit(0.04, "npc"),
    x1 = unit(0.96, "npc"),
    y0 = unit(0.885, "npc"),
    y1 = unit(0.885, "npc"),
    gp = gpar(col = HAIRLINE, lwd = 1)
  )

  ggdraw() +
    draw_plot(map_plot, x = 0.04, y = 0.14, width = 0.88, height = 0.72) +
    draw_plot(build_legend_plot(unit_type_counts), x = 0.04, y = 0.03, width = 0.36, height = 0.085) +
    draw_plot(build_scale_plot(), x = 0.74, y = 0.03, width = 0.18, height = 0.085) +
    draw_plot(build_arrow_plot(), x = 0.915, y = 0.78, width = 0.055, height = 0.12) +
    draw_label(
      "NWFP Management Groups of Bhutan",
      x = 0.04,
      y = 0.965,
      hjust = 0,
      vjust = 1,
      size = 22,
      fontface = "bold",
      color = TEXT_DARK,
      family = "sans"
    ) +
    draw_label(
      "National distribution by managing authority",
      x = 0.04,
      y = 0.935,
      hjust = 0,
      vjust = 1,
      size = 10.8,
      color = TEXT_MID,
      family = "sans"
    ) +
    draw_label(
      metrics_line,
      x = 0.04,
      y = 0.905,
      hjust = 0,
      vjust = 1,
      size = 11,
      color = TEXT_DARK,
      family = "sans"
    ) +
    draw_grob(header_rule, x = 0, y = 0, width = 1, height = 1) +
    draw_label(
      "Source layers in repository: NWFP group shapefiles and Dzongkhag Boundary. CRS: EPSG:5266 (Bhutan National Grid).",
      x = 0.04,
      y = 0.012,
      hjust = 0,
      vjust = 0,
      size = 8.3,
      color = TEXT_MID,
      family = "sans"
    )
}

export_outputs <- function(inventory, groups, boundary, missing) {
  dir.create(OUTPUT_DATA_DIR, recursive = TRUE, showWarnings = FALSE)

  write_csv(inventory, file.path(OUTPUT_DATA_DIR, "nwfp_tree_inventory.csv"))
  if (nrow(missing)) {
    write_csv(missing, file.path(OUTPUT_DATA_DIR, "nwfp_tree_missing_layers.csv"))
  }

  gpkg_path <- file.path(OUTPUT_DATA_DIR, "nwfp_management_groups_bhutan.gpkg")
  if (file.exists(gpkg_path)) {
    file.remove(gpkg_path)
  }
  st_write(groups, gpkg_path, layer = "nwfp_groups", quiet = TRUE)
  st_write(boundary, gpkg_path, layer = "dzongkhag_boundary", quiet = TRUE, append = TRUE)

  gpkg_path
}

save_map_outputs <- function(map_plot) {
  dir.create(OUTPUT_FIGURE_DIR, recursive = TRUE, showWarnings = FALSE)

  png_path <- file.path(OUTPUT_FIGURE_DIR, PUBLICATION_PNG_NAME)
  pdf_path <- file.path(OUTPUT_FIGURE_DIR, PUBLICATION_PDF_NAME)
  pdf_device <- if (capabilities("cairo")) cairo_pdf else pdf

  ggsave(
    filename = png_path,
    plot = map_plot,
    width = 14,
    height = 9,
    units = "in",
    dpi = 600,
    bg = BACKGROUND
  )
  ggsave(
    filename = pdf_path,
    plot = map_plot,
    width = 14,
    height = 9,
    units = "in",
    device = pdf_device,
    bg = BACKGROUND
  )

  c(png_path, pdf_path)
}

main <- function() {
  inventory <- parse_tree_inventory(TREE_FILE)
  metadata <- load_metadata(META_FILE)
  boundary <- load_boundary_layer()
  groups_result <- load_group_layers(inventory, metadata)
  groups <- groups_result$groups
  missing <- groups_result$missing

  gpkg_path <- export_outputs(inventory, groups, boundary, missing)
  map_plot <- compose_map_page(groups, boundary)
  map_paths <- save_map_outputs(map_plot)

  message("Parsed ", nrow(inventory), " tree-listed groups.")
  message("Mapped ", nrow(groups), " groups from shapefiles.")
  message("Missing or unmapped groups: ", nrow(missing), ".")
  for (map_path in map_paths) {
    message("Saved map: ", map_path)
  }
  message("Saved data package: ", gpkg_path)
}

main()
