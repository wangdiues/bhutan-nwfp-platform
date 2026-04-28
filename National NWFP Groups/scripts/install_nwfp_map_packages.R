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

if (!length(missing_packages)) {
  message("All required packages are already installed.")
  quit(save = "no", status = 0)
}

install.packages(missing_packages, repos = "https://cloud.r-project.org")

still_missing <- missing_packages[
  !vapply(missing_packages, requireNamespace, logical(1), quietly = TRUE)
]

if (length(still_missing)) {
  stop(
    sprintf(
      "Some packages are still missing after installation: %s",
      paste(still_missing, collapse = ", ")
    ),
    call. = FALSE
  )
}

message("Installed packages: ", paste(missing_packages, collapse = ", "))
