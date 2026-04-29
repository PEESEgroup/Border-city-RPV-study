import argparse
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import numpy as np


DEFAULT_BORDER_PAIRS = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]

CITY_DISPLAY_NAMES = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "nice": "Nice",
    "monaco": "Monaco",
}


def parse_pairs_arg(pairs_arg: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for item in pairs_arg.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid pair format: {item}. Use cityA:cityB,cityC:cityD")
        pairs.append((parts[0].strip().lower(), parts[1].strip().lower()))
    return pairs


def _display_city_name(city: str) -> str:
    return CITY_DISPLAY_NAMES.get(city.lower(), city.replace("_", " ").title())


def _read_geo(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    gdf = gpd.read_file(path)
    if gdf.empty:
        return gdf
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf


def _ensure_same_crs(gdf: gpd.GeoDataFrame, crs) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    if gdf.crs != crs:
        return gdf.to_crs(crs)
    return gdf


def _pad_bounds(bounds, pad_ratio: float = 0.03):
    minx, miny, maxx, maxy = bounds
    dx = maxx - minx
    dy = maxy - miny
    pad_x = max(dx * pad_ratio, 1e-5)
    pad_y = max(dy * pad_ratio, 1e-5)
    return (minx - pad_x, miny - pad_y, maxx + pad_x, maxy + pad_y)


def _compute_bounds(parts: List[gpd.GeoDataFrame], pad_ratio: float):
    valid_parts = [gdf for gdf in parts if not gdf.empty]
    if not valid_parts:
        return None
    crs = valid_parts[0].crs
    extent_gdf = gpd.GeoDataFrame(
        geometry=gpd.GeoSeries([geom for gdf in valid_parts for geom in gdf.geometry], crs=crs),
        crs=crs,
    )
    return _pad_bounds(extent_gdf.total_bounds, pad_ratio=pad_ratio)


def _choose_plot_crs(parts: List[gpd.GeoDataFrame]):
    valid_parts = [gdf for gdf in parts if not gdf.empty and gdf.crs is not None]
    if not valid_parts:
        return None
    src_crs = valid_parts[0].crs
    # If already projected, keep it.
    if not getattr(src_crs, "is_geographic", False):
        return src_crs
    try:
        extent_gdf = gpd.GeoDataFrame(
            geometry=gpd.GeoSeries([geom for gdf in valid_parts for geom in gdf.geometry], crs=src_crs),
            crs=src_crs,
        )
        utm_crs = extent_gdf.estimate_utm_crs()
        return utm_crs or src_crs
    except Exception:
        return src_crs


def _simplify_for_plot(gdf: gpd.GeoDataFrame, tol: float) -> gpd.GeoDataFrame:
    if gdf.empty or tol <= 0:
        return gdf
    out = gdf.copy()
    out = out.set_geometry(out.geometry.name)
    out[out.geometry.name] = out.geometry.simplify(tol, preserve_topology=True)
    return out


def _filter_matched_pv_rows(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    if "building_idx" not in gdf.columns:
        return gdf.iloc[0:0].copy()
    idx = gdf["building_idx"]
    # Keep rows with a valid building index (non-null and parseable as a number).
    matched_mask = idx.notna()
    if matched_mask.any():
        numeric_idx = gpd.pd.to_numeric(idx, errors="coerce")
        matched_mask = matched_mask & numeric_idx.notna()
    return gdf.loc[matched_mask].copy()


def _unique_building_footprints_from_pv_rows(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Use all rows to derive unique building footprints for background plotting."""
    if gdf.empty:
        return gdf
    out = gdf.copy()
    if "building_idx" in out.columns:
        valid_idx = gpd.pd.to_numeric(out["building_idx"], errors="coerce")
        has_idx = valid_idx.notna()
        with_idx = out.loc[has_idx].copy()
        without_idx = out.loc[~has_idx].copy()
        if not with_idx.empty:
            with_idx = with_idx.assign(_building_idx_num=valid_idx.loc[has_idx].to_numpy())
            with_idx = with_idx.drop_duplicates(subset=["_building_idx_num"]).drop(columns=["_building_idx_num"])
        out = gpd.pd.concat([with_idx, without_idx], ignore_index=True)
        out = gpd.GeoDataFrame(out, geometry=gdf.geometry.name, crs=gdf.crs)
    return out


def _extract_heat_points(gdf: gpd.GeoDataFrame) -> np.ndarray:
    if gdf.empty:
        return np.empty((0, 2), dtype=float)
    pts = gdf.geometry.representative_point()
    valid = pts.notna() & (~pts.is_empty)
    if not valid.any():
        return np.empty((0, 2), dtype=float)
    pts = pts.loc[valid]
    return np.column_stack([pts.x.to_numpy(dtype=float), pts.y.to_numpy(dtype=float)])


def _compute_kde_density(
    gdf: gpd.GeoDataFrame,
    bounds,
    kde_sigma_px: float,
    kde_sigma_m: float | None = None,
):
    pts = _extract_heat_points(gdf)
    if pts.shape[0] == 0:
        return None, pts
    xmin, ymin, xmax, ymax = bounds
    if not np.isfinite([xmin, ymin, xmax, ymax]).all():
        return None, pts

    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        gaussian_filter = None

    grid_x = 280
    span_x = max(xmax - xmin, 1e-9)
    span_y = max(ymax - ymin, 1e-9)
    grid_y = max(120, int(round(grid_x * (span_y / span_x))))

    hist, _, _ = np.histogram2d(
        pts[:, 0],
        pts[:, 1],
        bins=(grid_x, grid_y),
        range=((xmin, xmax), (ymin, ymax)),
    )

    density = hist.T  # imshow expects rows=y, cols=x
    if gaussian_filter is not None:
        sigma = float(kde_sigma_px)
        if kde_sigma_m is not None:
            cell_w = span_x / max(grid_x, 1)
            cell_h = span_y / max(grid_y, 1)
            cell_size = max((cell_w + cell_h) / 2.0, 1e-9)
            sigma = float(kde_sigma_m) / cell_size
        if sigma <= 0:
            return density, pts
        density = gaussian_filter(density, sigma=sigma, mode="constant")
    return density, pts


def _plot_kde_heatmap(ax, density, pts, bounds, cmap: str, vmax: float, max_alpha: float = 0.8) -> None:
    if density is None:
        if pts is not None and pts.shape[0] > 0:
            ax.scatter(pts[:, 0], pts[:, 1], s=2.0, c="#666666", alpha=0.5, linewidths=0, zorder=3)
        return

    if not np.isfinite(vmax) or vmax <= 0:
        # Fallback for tiny samples: plot points if KDE image is degenerate.
        ax.scatter(pts[:, 0], pts[:, 1], s=2.0, c="#666666", alpha=0.5, linewidths=0, zorder=3)
        return

    xmin, ymin, xmax, ymax = bounds
    density_norm = np.clip(density, 0, vmax) / vmax
    alpha = np.where(density_norm > 0, np.power(density_norm, 0.65) * max_alpha, 0.0)
    ax.imshow(
        density_norm,
        extent=(xmin, xmax, ymin, ymax),
        origin="lower",
        cmap=cmap,
        interpolation="bilinear",
        alpha=alpha,
        zorder=2,
        aspect="auto",
    )


def _crop_to_bounds(gdf: gpd.GeoDataFrame, bounds) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    xmin, ymin, xmax, ymax = bounds
    try:
        return gdf.cx[xmin:xmax, ymin:ymax]
    except Exception:
        return gdf


def plot_pair_map(
    city_a: str,
    city_b: str,
    prediction_root: Path,
    boundary_root: Path,
    building_root: Path,
    output_dir: Path,
    simplify_tol: float,
    kde_sigma_px: float,
    kde_sigma_m: float | None,
    show_pv: bool,
    show_buildings: bool,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is required to plot maps. Install with: pip install matplotlib"
        ) from exc

    paths = {
        "pv_a": prediction_root / city_a / "processed_on_bldg.geojson",
        "pv_b": prediction_root / city_b / "processed_on_bldg.geojson",
        "bdry_a": boundary_root / f"{city_a}.geojson",
        "bdry_b": boundary_root / f"{city_b}.geojson",
        "bldg_a": building_root / f"{city_a}.geojson",
        "bldg_b": building_root / f"{city_b}.geojson",
    }
    required_keys = ["pv_a", "pv_b", "bdry_a", "bdry_b"]
    if show_buildings:
        required_keys.extend(["bldg_a", "bldg_b"])
    missing = [k for k in required_keys if not paths[k].exists()]
    if missing:
        print(f"[skip] Missing files for {city_a}-{city_b}: {', '.join(missing)}")
        return

    bdry_a = _read_geo(paths["bdry_a"])
    bdry_b = _read_geo(paths["bdry_b"])
    if show_buildings:
        bldg_a_bg = _read_geo(paths["bldg_a"])
        bldg_b_bg = _read_geo(paths["bldg_b"])
    else:
        bldg_a_bg = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        bldg_b_bg = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    pv_a = _read_geo(paths["pv_a"]) if show_pv else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    pv_b = _read_geo(paths["pv_b"]) if show_pv else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    pv_a_matched = _filter_matched_pv_rows(pv_a) if show_pv else pv_a
    pv_b_matched = _filter_matched_pv_rows(pv_b) if show_pv else pv_b

    base_crs = None
    for gdf in [bdry_a, bdry_b, pv_a, pv_b]:
        if not gdf.empty and gdf.crs is not None:
            base_crs = gdf.crs
            break
    if base_crs is None:
        base_crs = "EPSG:4326"

    bdry_a = _ensure_same_crs(bdry_a, base_crs)
    bdry_b = _ensure_same_crs(bdry_b, base_crs)
    pv_a = _ensure_same_crs(pv_a, base_crs)
    pv_b = _ensure_same_crs(pv_b, base_crs)
    pv_a_matched = _ensure_same_crs(pv_a_matched, base_crs)
    pv_b_matched = _ensure_same_crs(pv_b_matched, base_crs)
    bldg_a_bg = _ensure_same_crs(bldg_a_bg, base_crs)
    bldg_b_bg = _ensure_same_crs(bldg_b_bg, base_crs)

    if simplify_tol > 0:
        bdry_a = _simplify_for_plot(bdry_a, simplify_tol)
        bdry_b = _simplify_for_plot(bdry_b, simplify_tol)
        bldg_a_bg = _simplify_for_plot(bldg_a_bg, simplify_tol)
        bldg_b_bg = _simplify_for_plot(bldg_b_bg, simplify_tol)

    # Reproject to a local projected CRS (meters) for visually correct x/y scale and KDE.
    plot_crs = _choose_plot_crs([bdry_a, bdry_b, bldg_a_bg, bldg_b_bg, pv_a, pv_b])
    if plot_crs is not None:
        bdry_a = _ensure_same_crs(bdry_a, plot_crs)
        bdry_b = _ensure_same_crs(bdry_b, plot_crs)
        pv_a = _ensure_same_crs(pv_a, plot_crs)
        pv_b = _ensure_same_crs(pv_b, plot_crs)
        pv_a_matched = _ensure_same_crs(pv_a_matched, plot_crs)
        pv_b_matched = _ensure_same_crs(pv_b_matched, plot_crs)
        bldg_a_bg = _ensure_same_crs(bldg_a_bg, plot_crs)
        bldg_b_bg = _ensure_same_crs(bldg_b_bg, plot_crs)

    if all(gdf.empty for gdf in [bdry_a, bdry_b, pv_a, pv_b]):
        print(f"[skip] No geometry to plot for {city_a}-{city_b}")
        return

    def _draw_and_save(
        pv_a_plot: gpd.GeoDataFrame,
        pv_b_plot: gpd.GeoDataFrame,
        suffix: str,
        title_suffix: str,
    ) -> None:
        # Prefer a PV-driven zoom so the PV density hotspots are visually larger.
        bounds = _compute_bounds([pv_a_plot, pv_b_plot], pad_ratio=0.10)
        if bounds is None:
            bounds = _compute_bounds([bdry_a, bdry_b], pad_ratio=0.02)
        if bounds is None:
            print(f"[skip] Could not determine bounds for {city_a}-{city_b} ({suffix})")
            return
        xmin, ymin, xmax, ymax = bounds

        fig, ax = plt.subplots(figsize=(10, 10), dpi=250)
        background_color = "#f0f0f0"
        fig.patch.set_facecolor(background_color)
        ax.set_facecolor(background_color)

        # Faint building footprints as context/background.
        if show_buildings and not bldg_a_bg.empty:
            print(f"  Plotting {len(bldg_a_bg)} building footprints for {city_a} background")
            bldg_a_bg.plot(
                ax=ax,
                facecolor="none",
                edgecolor="#8f8f8f",
                linewidth=0.2,
                alpha=0.1,
                zorder=0,
            )
        if show_buildings and not bldg_b_bg.empty:
            bldg_b_bg.plot(
                ax=ax,
                facecolor="none",
                edgecolor="#8f8f8f",
                linewidth=0.2,
                alpha=0.1,
                zorder=0,
            )

        # Plain, subtle boundaries only.
        if not bdry_a.empty:
            _crop_to_bounds(bdry_a, bounds).boundary.plot(
                ax=ax, color="#4a4a4a", linewidth=0.9, alpha=0.35, zorder=1
            )
        if not bdry_b.empty:
            _crop_to_bounds(bdry_b, bounds).boundary.plot(
                ax=ax, color="#4a4a4a", linewidth=0.9, alpha=0.35, zorder=1
            )

        if show_pv:
            density_a, pts_a = (
                _compute_kde_density(pv_a_plot, bounds, kde_sigma_px=kde_sigma_px)
                if kde_sigma_m is None
                else _compute_kde_density(
                    pv_a_plot, bounds, kde_sigma_px=kde_sigma_px, kde_sigma_m=kde_sigma_m
                )
                if not pv_a_plot.empty
                else (None, None)
            )
            density_b, pts_b = (
                _compute_kde_density(pv_b_plot, bounds, kde_sigma_px=kde_sigma_px)
                if kde_sigma_m is None
                else _compute_kde_density(
                    pv_b_plot, bounds, kde_sigma_px=kde_sigma_px, kde_sigma_m=kde_sigma_m
                )
                if not pv_b_plot.empty
                else (None, None)
            )

            combined = []
            if density_a is not None and density_a.size:
                combined.append(density_a.ravel())
            if density_b is not None and density_b.size:
                combined.append(density_b.ravel())
            if combined:
                combined_vals = np.concatenate(combined)
                combined_vals = combined_vals[np.isfinite(combined_vals)]
                combined_vals = combined_vals[combined_vals > 0]
                shared_vmax = float(np.nanpercentile(combined_vals, 99.5)) if combined_vals.size else 0.0
            else:
                shared_vmax = 0.0

            _plot_kde_heatmap(
                ax=ax, density=density_a, pts=pts_a, bounds=bounds, cmap="Blues", vmax=shared_vmax, max_alpha=0.80
            )
            _plot_kde_heatmap(
                ax=ax, density=density_b, pts=pts_b, bounds=bounds, cmap="Greens", vmax=shared_vmax, max_alpha=0.75
            )

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()
        display_city_a = _display_city_name(city_a)
        display_city_b = _display_city_name(city_b)
        # ax.set_title(f"{display_city_a} - {display_city_b}", fontsize=18, pad=6)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{city_a}_{city_b}_heatmap_{suffix}.pdf"
        fig.tight_layout(pad=0.1)
        fig.savefig(out_path, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)
        print(f"[ok] Saved {out_path}")

    _draw_and_save(pv_a_matched, pv_b_matched, "matched_pv_rows", "matched PV rows")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot border city-pair KDE heatmaps with boundary outlines."
    )
    parser.add_argument(
        "--prediction-root",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/prediction"),
        help="Root directory containing {city}/processed_on_bldg.geojson",
    )
    parser.add_argument(
        "--boundary-root",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/data/boundary"),
        help="Directory containing {city}.geojson boundary polygons",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/prediction/heatmaps"),
        help="Directory to save output images",
    )
    parser.add_argument(
        "--building-root",
        type=Path,
        default=Path("/datasets/joe/dataset/Border/data/buildings_merged"),
        help="Directory containing merged building footprints as {city}.geojson",
    )
    parser.add_argument(
        "--pairs",
        type=str,
        default="",
        help="Override pairs, format: cityA:cityB,cityC:cityD",
    )
    parser.add_argument(
        "--simplify-tol",
        type=float,
        default=0.00005,
        help="Simplify tolerance for boundary/building background geometry in CRS units",
    )
    parser.add_argument(
        "--kde-sigma-px",
        type=float,
        default=8.0,
        help="Gaussian KDE smoothing sigma in heatmap grid pixels (<=0 disables smoothing)",
    )
    parser.add_argument(
        "--kde-sigma-m",
        type=float,
        default=None,
        help="Gaussian KDE smoothing sigma in meters (overrides --kde-sigma-px; <=0 disables smoothing)",
    )
    parser.add_argument(
        "--hide-pv",
        action="store_true",
        help="Do not overlay PV heatmaps; plot only boundary outlines",
    )
    parser.add_argument(
        "--hide-buildings",
        action="store_true",
        help="Do not draw building-footprint background layer",
    )
    args = parser.parse_args()

    pairs = parse_pairs_arg(args.pairs) if args.pairs.strip() else DEFAULT_BORDER_PAIRS
    for city_a, city_b in pairs:
        plot_pair_map(
            city_a=city_a,
            city_b=city_b,
            prediction_root=args.prediction_root,
            boundary_root=args.boundary_root,
            building_root=args.building_root,
            output_dir=args.output_dir,
            simplify_tol=args.simplify_tol,
            kde_sigma_px=args.kde_sigma_px,
            kde_sigma_m=args.kde_sigma_m,
            show_pv=not args.hide_pv,
            show_buildings=not args.hide_buildings,
        )


if __name__ == "__main__":
    main()
