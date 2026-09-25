# HRL Imperviousness — Time Series Reconstruction (Change Backcalculation)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/copernicus-land/clms_nvlcc_backcalculation/HEAD?urlpath=%2Fdoc%2Ftree%2Fchange_backcalculation.ipynb)

## Overview

This repository contains a Jupyter Notebook demonstrating a method for reconstructing
spatially consistent historical **Imperviousness Density (IMD)** layers of the CLMS
**High-Resolution Layer Imperviousness (HRL Imperviousness)**, using the most recent (and most accurate)
status layer as a baseline together with the **Imperviousness Density Change (IMDC)**
layers.

The notebook shows why the intuitive approach — subtracting detected change backwards in
time — produces physically impossible values (e.g. negative imperviousness), and introduces
a robust alternative: **binary mask substitution**, which uses the change layers only as a
switch ("did this pixel change?") rather than as a quantity to subtract.

## Features

- Interactive site selection (Innsbruck at 10 m, North Italy at 100 m) with an overview map.
- Side-by-side visualisation of the two reconstruction methods and their pixel-value
  distributions.
- Interactive `folium` map to toggle between the original, subtraction, and binary-mask
  substitution layers for any reconstructed year.
- A discussion of the limitations of the method and when it should (not) be used.

## Getting Started

### Launch via Binder

The easiest way to explore the notebook — no installation required:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/copernicus-land/clms_nvlcc_backcalculation/HEAD?urlpath=%2Fdoc%2Ftree%2Fchange_backcalculation.ipynb)

The first launch can take a few minutes while Binder builds the environment; subsequent
launches are faster thanks to caching.

### Launch locally

Clone the repository:

```
git clone https://github.com/copernicus-land/clms_nvlcc_backcalculation.git
cd clms_nvlcc_backcalculation
```

Create the conda environment from `environment.yml` (this includes GDAL, which is easiest
to install via conda-forge):

```
conda env create -f environment.yml
conda activate nvlcc-backcalculation
```

Then launch Jupyter and open the notebook:

```
jupyter lab
```

## Repository Structure

- `change_backcalculation.ipynb` – main notebook. Focuses on the idea: site selection, the
  two reconstruction methods, and their comparison; loading, plotting, and widget boilerplate
  live in `helpers/`.
- `helpers/raster_utils.py` – raster I/O, resampling, and image-conversion functions.
- `helpers/data_loading.py` – site definitions and status/change raster loading.
- `helpers/analysis.py` – invalid-pixel summary used to compare the two methods.
- `helpers/plotting.py` – all matplotlib/folium map and chart builders.
- `helpers/ui.py` – dropdown-selector widget factory.
- `data/` – small demo dataset: cropped IMD/IMDC GeoTIFFs for two study areas (Innsbruck,
  North Italy) plus `site_definition.yaml`, which defines their extents and resolutions.
- `environment.yml` – conda environment definition (used both locally and by Binder).

## Data

The `data/` folder contains a small cropped subset of the Imperviousness Density (IMD) and
Imperviousness Density Change (IMDC) layers of the CLMS **HRL Imperviousness**, provided only to make this notebook
self-contained and runnable. It is not the full dataset.
