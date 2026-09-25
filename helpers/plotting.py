"""Map and chart builders for the change-backcalculation notebook.

Keeps matplotlib/folium styling out of the narrative cells so each notebook
cell can focus on one idea instead of plotting boilerplate.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
import folium
from folium.raster_layers import ImageOverlay

from .raster_utils import array_to_img

IMD_CMAP = 'YlOrRd'
NEGATIVE_COLOR = '#2f3fd4'  # blue: impossible negative imperviousness
OVER_COLOR = '#c41bc4'      # magenta: above 100 %


def _imd_cmap():
    cmap = plt.get_cmap(IMD_CMAP).copy()
    cmap.set_bad('#cccccc')  # grey for nodata pixels
    return cmap


def _figsize_for(arr, width=14):
    aspect = arr.shape[0] / arr.shape[1]
    return width, max(2.5, width * aspect)


def _out_of_range_overlay(arr, alpha=0.8):
    """RGBA layer highlighting pixels below 0 % (blue) or above 100 % (magenta)."""
    rgba = np.zeros((*arr.shape, 4), dtype=float)
    rgba[(~np.isnan(arr)) & (arr < 0)] = to_rgba(NEGATIVE_COLOR, alpha)
    rgba[(~np.isnan(arr)) & (arr > 100)] = to_rgba(OVER_COLOR, alpha)
    return rgba


def _out_of_range_legend():
    return [
        mpatches.Patch(color=NEGATIVE_COLOR, label='Impossible negative  (< 0 %)'),
        mpatches.Patch(color=OVER_COLOR, label='Above maximum  (> 100 %)'),
    ]


def plot_site_overview(clat, clon, zoom, bounds, site_name):
    """Interactive folium map showing where the study area sits in Europe."""
    m = folium.Map(location=[clat, clon], zoom_start=zoom, tiles='OpenStreetMap')
    folium.Rectangle(
        bounds=bounds, color='#c62828', weight=2.5,
        fill=True, fill_color='#ef5350', fill_opacity=0.12,
        tooltip=f'{site_name} study area',
    ).add_to(m)
    folium.Marker(
        [clat, clon], icon=folium.Icon(color='red', icon='info-sign'), tooltip=site_name,
    ).add_to(m)
    return m


def plot_status_map(arr, title, width=10):
    """Single IMD status map on a shared 0-100 % colour scale."""
    fig, ax = plt.subplots(figsize=_figsize_for(arr, width))
    im = ax.imshow(np.ma.masked_invalid(arr), cmap=_imd_cmap(), vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, shrink=0.7, label='Imperviousness (%)')
    ax.set_title(title, fontsize=13)
    ax.axis('off')
    plt.tight_layout()
    plt.show()


def plot_subtraction_maps(results, invalid, years, site_name):
    """Per-year subtraction-result maps with out-of-range pixels highlighted."""
    for year in years:
        arr = results[year]
        fig, ax = plt.subplots(figsize=_figsize_for(arr))
        im = ax.imshow(np.ma.masked_invalid(np.clip(arr, 0, 100)), cmap=_imd_cmap(), vmin=0, vmax=100)
        plt.colorbar(im, ax=ax, shrink=0.7, label='%')
        ax.imshow(_out_of_range_overlay(arr, alpha=0.82))

        n_inv, _, pct = invalid[year]
        ax.set_title(
            f'Backward Subtraction — 20{year}   ({n_inv:,} invalid px, {pct:.1f} %)\n'
            'blue = negative imperviousness   |   magenta = above 100 %',
            fontsize=12,
        )
        ax.axis('off')
        ax.legend(handles=_out_of_range_legend(), loc='lower right', fontsize=9, framealpha=0.9)
        plt.tight_layout()
        plt.show()


def plot_subtraction_histograms(results, years):
    """Per-year pixel-value distributions, highlighting out-of-range tails."""
    shared_max, x_lo, x_hi = 0, -100, 100
    for year in years:
        flat = results[year].flatten()
        x_lo = min(x_lo, np.nanmin(flat))
        x_hi = max(x_hi, np.nanmax(flat))
        interior = flat[(flat > 0) & (flat < 100)]
        if len(interior):
            counts, _ = np.histogram(interior, bins=48, range=(1, 99))
            shared_max = max(shared_max, counts.max())

    for year in years:
        flat = results[year].flatten()
        flat = flat[~np.isnan(flat)]
        valid = flat[(flat >= 0) & (flat <= 100)]
        neg = flat[flat < 0]
        over = flat[flat > 100]

        fig, ax = plt.subplots(figsize=(14, 4))
        ax.hist(valid, bins=50, range=(0, 100), color='#777', alpha=0.7, label='Valid (0–100 %)')
        if len(neg):
            ax.hist(neg, bins=20, color=NEGATIVE_COLOR, alpha=0.85, label=f'Negative: {len(neg):,} px')
        if len(over):
            ax.hist(over, bins=20, color=OVER_COLOR, alpha=0.85, label=f'>100 %: {len(over):,} px')

        # Rug marks keep sparse out-of-range pixels visible next to the tall valid bars
        for vals, color in [(neg, NEGATIVE_COLOR), (over, OVER_COLOR)]:
            ax.plot(vals, np.zeros_like(vals), '|', color=color, ms=18, mew=1, clip_on=False)

        ax.set_ylim(0, shared_max * 1.2)
        ax.set_xlim(x_lo - 5, x_hi + 5)
        ax.axvline(0, color='black', lw=1.5, ls='--', alpha=0.8)
        ax.axvline(100, color='black', lw=1.5, ls=':', alpha=0.8)
        ax.set_title(f'Pixel Value Distribution — Backward Subtraction 20{year}', fontsize=12)
        ax.set_xlabel('IMD value (%)')
        ax.set_ylabel('Pixel count')
        ax.legend(fontsize=9)
        plt.tight_layout()
        plt.show()


def plot_method_comparison(orig, sub, ind, invalid_info, year):
    """Original / subtraction / binary-mask-substitution maps, plus their difference."""
    n_inv, _, pct = invalid_info
    aspect = orig.shape[0] / orig.shape[1]
    row_h = max(2.5, 14 * aspect)
    fig, axes = plt.subplots(4, 1, figsize=(14, row_h * 4))
    cmap = _imd_cmap()

    panels = [
        (orig, f'Original IMD 20{year}'),
        (sub, f'Subtraction 20{year}  ({n_inv:,} invalid px, {pct:.1f} %)'),
        (ind, f'Binary Mask Substitution 20{year}'),
    ]
    for ax, (arr, title) in zip(axes[:3], panels):
        im = ax.imshow(np.ma.masked_invalid(np.clip(arr, 0, 100)), cmap=cmap, vmin=0, vmax=100)
        plt.colorbar(im, ax=ax, shrink=0.7, label='%')
        ax.set_title(title, fontsize=12)
        ax.axis('off')
        if 'Subtraction' in title:
            ax.imshow(_out_of_range_overlay(arr, alpha=0.78))
            ax.legend(handles=_out_of_range_legend(), loc='lower right', fontsize=9, framealpha=0.9)

    diff = ind - sub
    dmax = np.nanmax(np.abs(diff)) if np.any(~np.isnan(diff)) else 1
    im_d = axes[3].imshow(diff, cmap='RdBu_r', vmin=-dmax, vmax=dmax)
    plt.colorbar(im_d, ax=axes[3], shrink=0.7, label='pp difference')
    axes[3].set_title(f'Difference — Binary Mask Substitution minus Subtraction 20{year}', fontsize=12)
    axes[3].axis('off')

    plt.tight_layout()
    plt.show()


def plot_invalid_pixel_counts(invalid, years, site_name):
    """Bar chart of invalid-pixel counts per reconstructed year (backward subtraction)."""
    fig, ax1 = plt.subplots(figsize=(8, 5))

    inv_counts = [invalid[y][0] for y in years]
    pct_labels = [f'{invalid[y][2]:.1f}%' for y in years]

    bars = ax1.bar(range(len(years)), inv_counts, color='#2f3fd4', alpha=0.50, label='Subtraction method')
    ax1.bar(range(len(years)), [0] * len(years), color='#27ae60', alpha=0.50,
            label='Binary mask substitution (always 0)')
    ax1.bar_label(bars, labels=pct_labels, padding=4, fontsize=9)
    ax1.set_xticks(range(len(years)))
    ax1.set_xticklabels([f'20{y}' for y in years])
    ax1.set_ylabel('Number of invalid pixels')
    ax1.set_title('Invalid Pixel Count per Reconstructed Year', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.set_ylim(0, max(max(inv_counts) * 1.20, 1))

    fig.text(
        0.5, -0.05,
        f'Pixel counts refer to the {site_name} study-area tile only (the extent shown in the maps above), '
        'not the full product coverage.',
        ha='center', fontsize=9, style='italic',
    )

    plt.tight_layout()
    plt.show()


def plot_year_distribution(status, sub_results, ind_results, year):
    """Pixel-value distribution comparison (original / subtraction / binary mask substitution) for one year."""
    fig, ax2 = plt.subplots(figsize=(8, 5))

    bins = np.linspace(-30, 110, 70)
    for arr, label, color in [
        (status[year][0], f'Original IMD 20{year}', '#888'),
        (sub_results[year], 'Subtraction', '#2f3fd4'),
        (ind_results[year], 'Binary mask substitution', '#27ae60'),
    ]:
        flat = arr.flatten()
        flat = flat[~np.isnan(flat)]
        ax2.hist(flat, bins=bins, alpha=0.55, color=color, label=label)

    ax2.axvline(0, color='black', lw=1.5, ls='--', alpha=0.8)
    ax2.axvline(100, color='black', lw=1.5, ls=':', alpha=0.8)
    ax2.set_xlabel('Imperviousness value (%)')
    ax2.set_ylabel('Pixel count')
    ax2.set_title(f'Pixel Distributions — 20{year}', fontsize=12)

    # Scale to the interior (1-99 %) distribution so the 0 %/100 % spikes don't dominate
    interior = status[year][0]
    interior = interior[~np.isnan(interior)]
    interior = interior[(interior > 0) & (interior < 100)]
    ref_counts, _ = np.histogram(interior, bins=48, range=(1, 99))
    ax2.set_ylim(0, ref_counts.max() * 1.2)
    ax2.legend(fontsize=10)

    plt.tight_layout()
    plt.show()


def plot_interactive_comparison(clat, clon, zoom, bounds, orig, sub, ind, year):
    """Folium map with original / subtraction / binary-mask-substitution as toggleable layers."""
    m = folium.Map(location=[clat, clon], zoom_start=zoom + 1)
    layers = [
        (orig, f'Original IMD 20{year}', {}),
        (sub, f'Subtraction 20{year}', {'clr_below_vmin': NEGATIVE_COLOR, 'clr_above_vmax': OVER_COLOR}),
        (ind, f'Binary Mask Substitution 20{year}', {}),
    ]
    for arr, name, kw in layers:
        ImageOverlay(
            image=array_to_img(arr, IMD_CMAP, 0, 100, **kw),
            bounds=bounds, opacity=1, name=name,
        ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m
