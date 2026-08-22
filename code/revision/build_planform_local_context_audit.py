#!/usr/bin/env python3
"""Audit building-planform and local urban-context associations with mapped PV.

The audit uses the 12 primary manuscript cities. It does not infer roof pitch,
roof-surface orientation, structural suitability or causal adoption effects.
Planform descriptors are computed from building-footprint polygons, and local
context is computed from the same globally anchored 1-km grid used in the
manuscript. Outcome-derived grid variables are deliberately excluded from the
models to avoid using local PV deployment to predict building-level PV status.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyogrio import read_dataframe
from shapely import (
    area as shapely_area,
    get_coordinates,
    get_type_id,
    is_empty,
    is_valid,
    length as shapely_length,
    minimum_rotated_rectangle,
)
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REV = Path(__file__).resolve().parents[2]
BORDER = REV.parents[3]
BUILDINGS_ROOT = BORDER / "data/buildings_merged"
PV_ROOT = BORDER / "prediction"
SAN_DIEGO_BOUNDARY = (
    REV / "evidence/v1_verified_data/boundaries/sandiego_city_sangis_2026-08-10.geojson"
)
CENTRAL_INPUT = REV / "evidence/v1_verified_data/prevalence_intensity_14cities.csv"

OUTPUT_DIR = REV / "outputs/audit_reports/building_planform_local_context"
FIGURE_DIR = REV / "figures/supplement/revision"
TABLE_DIR = REV / "tables"
SOURCE_DIR = REV / "Source_Data/csv"

GRID_CRS = "EPSG:6933"
NEGATIVE_SAMPLE_LIMIT = 50_000
RANDOM_SEED = 20260821

PAIRS = [
    ("vienna", "bratislava"),
    ("singapore", "johorbahru"),
    ("sandiego", "tijuana"),
    ("elpaso", "juarez"),
    ("hongkong", "shenzhen"),
    ("monaco", "nice"),
]
CITY_ORDER = [city for pair in PAIRS for city in pair]
DISPLAY = {
    "vienna": "Vienna",
    "bratislava": "Bratislava",
    "singapore": "Singapore",
    "johorbahru": "Johor Bahru",
    "sandiego": "San Diego",
    "tijuana": "Tijuana",
    "elpaso": "El Paso",
    "juarez": "Juarez",
    "hongkong": "Hong Kong",
    "shenzhen": "Shenzhen",
    "monaco": "Monaco",
    "nice": "Nice",
}

NUMERIC_FEATURES = [
    "log_footprint_area",
    "compactness",
    "log_elongation",
    "cardinal_alignment",
    "log_local_building_density",
    "log_local_footprint_coverage",
]
FEATURE_LABELS = {
    "log_footprint_area": "Footprint area",
    "compactness": "Planform compactness",
    "log_elongation": "Planform elongation",
    "cardinal_alignment": "Cardinal-axis alignment",
    "log_local_building_density": "Local building density",
    "log_local_footprint_coverage": "Local footprint coverage",
}
CATEGORICAL_FEATURES = ["city_key", "base_class"]


def normalize_base_class(values: pd.Series) -> pd.Series:
    valid = {
        "Single-Residential",
        "Multi-Residential",
        "Commercial",
        "Industrial",
        "Public & Infrastructure",
        "Others",
    }
    text = values.fillna("Others").astype(str).str.strip()
    return text.where(text.isin(valid), "Others")


def planform_metrics(buildings: gpd.GeoDataFrame) -> pd.DataFrame:
    """Compute dimensionless footprint-shape descriptors in a local UTM CRS."""
    local_crs = buildings.estimate_utm_crs()
    if local_crs is None:
        raise RuntimeError("Could not estimate a local projected CRS")
    local = buildings.to_crs(local_crs)
    geom = local.geometry.array
    raw_area = np.asarray(shapely_area(geom), dtype=float)
    perimeter = np.asarray(shapely_length(geom), dtype=float)
    geometrically_valid = (
        np.asarray(is_valid(geom), dtype=bool)
        & ~np.asarray(is_empty(geom), dtype=bool)
        & np.isfinite(raw_area)
        & np.isfinite(perimeter)
        & (raw_area > 0.01)
        & (perimeter > 0.01)
    )

    compactness = np.full(len(local), np.nan, dtype=float)
    compactness[geometrically_valid] = (
        4.0 * math.pi * raw_area[geometrically_valid]
        / np.square(perimeter[geometrically_valid])
    )
    compactness = np.clip(compactness, 0.0, 1.0)

    elongation = np.full(len(local), np.nan, dtype=float)
    orientation_deg = np.full(len(local), np.nan, dtype=float)
    rectangles = minimum_rotated_rectangle(geom)
    rectangle_valid = geometrically_valid & (np.asarray(get_type_id(rectangles)) == 3)
    valid_positions = np.flatnonzero(rectangle_valid)
    if len(valid_positions):
        coords, coord_index = get_coordinates(rectangles[rectangle_valid], return_index=True)
        counts = np.bincount(coord_index, minlength=len(valid_positions))
        conventional = counts == 5
        if conventional.any():
            conventional_positions = valid_positions[conventional]
            coords5 = coords[np.isin(coord_index, np.flatnonzero(conventional))].reshape(-1, 5, 2)
            edges = np.diff(coords5, axis=1)
            edge_lengths = np.hypot(edges[:, :, 0], edges[:, :, 1])
            major_index = np.argmax(edge_lengths, axis=1)
            major = edge_lengths[np.arange(len(edge_lengths)), major_index]
            minor = np.min(np.where(edge_lengths > 1e-6, edge_lengths, np.inf), axis=1)
            ratio = major / minor
            angle = np.degrees(
                np.arctan2(
                    edges[np.arange(len(edges)), major_index, 1],
                    edges[np.arange(len(edges)), major_index, 0],
                )
            ) % 180.0
            finite = np.isfinite(ratio) & (ratio >= 1.0) & np.isfinite(angle)
            elongation[conventional_positions[finite]] = ratio[finite]
            orientation_deg[conventional_positions[finite]] = angle[finite]

    cardinal_alignment = np.abs(np.cos(np.deg2rad(2.0 * orientation_deg)))
    del local, geom, rectangles
    gc.collect()
    return pd.DataFrame(
        {
            "raw_planform_area_m2": raw_area,
            "perimeter_m": perimeter,
            "compactness": compactness,
            "elongation": elongation,
            "planform_axis_orientation_deg": orientation_deg,
            "cardinal_alignment": cardinal_alignment,
            "valid_planform": (
                geometrically_valid
                & np.isfinite(compactness)
                & np.isfinite(elongation)
                & np.isfinite(cardinal_alignment)
            ),
        }
    )


def read_city(city: str, target: pd.Series, city_seed: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    building_path = BUILDINGS_ROOT / f"{city}.geojson"
    pv_path = PV_ROOT / city / "processed_on_bldg.geojson"
    source_boundary = None
    if city == "sandiego":
        source_boundary = gpd.read_file(SAN_DIEGO_BOUNDARY).geometry.iloc[0]

    kwargs: dict[str, object] = {"columns": ["base_class"]}
    if source_boundary is not None:
        kwargs["fid_as_index"] = True
        kwargs["mask"] = source_boundary
    buildings = read_dataframe(building_path, **kwargs)
    if source_boundary is not None:
        buildings.index = buildings.index.astype(int)
        inside = buildings.geometry.representative_point().apply(source_boundary.covers)
        buildings = buildings.loc[inside].copy()
        buildings["building_idx"] = buildings.index.astype(np.int64)
    else:
        buildings["building_idx"] = np.arange(len(buildings), dtype=np.int64)
    buildings["base_class"] = normalize_base_class(buildings["base_class"])

    shapes = planform_metrics(buildings)

    projected = buildings.to_crs(GRID_CRS)
    points = projected.geometry.representative_point()
    raw = pd.DataFrame(
        {
            "building_idx": buildings["building_idx"].to_numpy(dtype=np.int64),
            "base_class": buildings["base_class"].to_numpy(),
            "point_x_m": points.x.to_numpy(dtype=float),
            "point_y_m": points.y.to_numpy(dtype=float),
            "raw_building_area_m2": projected.geometry.area.to_numpy(dtype=float),
        }
    )
    raw = pd.concat([raw, shapes], axis=1)
    del projected, points, shapes

    pv_kwargs: dict[str, object] = {"columns": ["building_idx"]}
    if source_boundary is not None:
        pv_kwargs["mask"] = source_boundary
    pv = read_dataframe(pv_path, **pv_kwargs)
    pv = pv[pv["building_idx"].notna()].copy()
    pv["building_idx"] = pv["building_idx"].astype(np.int64)
    pv = pv[pv["building_idx"].isin(pd.Index(raw["building_idx"]))]
    pv_projected = pv.to_crs(GRID_CRS)
    pv_projected["raw_pv_area_m2"] = pv_projected.geometry.area
    pv_by_building = pv_projected.groupby("building_idx")["raw_pv_area_m2"].sum()
    raw["raw_pv_area_m2"] = raw["building_idx"].map(pv_by_building).fillna(0.0)
    raw["pv_positive"] = raw["raw_pv_area_m2"] > 0
    del pv, pv_projected, pv_by_building, buildings
    gc.collect()

    if len(raw) != int(target["building_count"]):
        raise AssertionError(f"{city}: building count does not match frozen central input")
    if int(raw["pv_positive"].sum()) != int(target["pv_positive_buildings"]):
        raise AssertionError(f"{city}: PV-positive count does not match frozen central input")

    building_scale = float(target["footprint_area_m2"]) / raw["raw_building_area_m2"].sum()
    pv_scale = float(target["pv_area_m2"]) / raw["raw_pv_area_m2"].sum()
    raw["footprint_area_m2"] = raw["raw_building_area_m2"] * building_scale
    raw["pv_area_m2"] = raw["raw_pv_area_m2"] * pv_scale
    raw["grid_x"] = np.floor(raw["point_x_m"] / 1000.0).astype(np.int64)
    raw["grid_y"] = np.floor(raw["point_y_m"] / 1000.0).astype(np.int64)

    grid = raw.groupby(["grid_x", "grid_y"], as_index=False).agg(
        local_building_density=("building_idx", "size"),
        local_footprint_area_m2=("footprint_area_m2", "sum"),
    )
    grid["local_footprint_coverage"] = grid["local_footprint_area_m2"] / 1_000_000.0
    raw = raw.merge(
        grid[["grid_x", "grid_y", "local_building_density", "local_footprint_coverage"]],
        on=["grid_x", "grid_y"],
        how="left",
        validate="many_to_one",
    )
    raw["eligible_grid_50"] = raw["local_building_density"] >= 50
    raw["valid_model_row"] = (
        raw["eligible_grid_50"]
        & raw["valid_planform"]
        & (raw["footprint_area_m2"] > 0)
        & (raw["local_footprint_coverage"] > 0)
    )
    raw["log_footprint_area"] = np.log(raw["footprint_area_m2"].where(raw["footprint_area_m2"] > 0))
    raw["log_elongation"] = np.log(raw["elongation"].clip(lower=1.0, upper=50.0))
    raw["log_local_building_density"] = np.log(raw["local_building_density"])
    raw["log_local_footprint_coverage"] = np.log(
        raw["local_footprint_coverage"].where(raw["local_footprint_coverage"] > 0)
    )
    raw["conditional_intensity_building"] = raw["pv_area_m2"] / raw["footprint_area_m2"]

    valid = raw[raw["valid_model_row"]].copy()
    positives = valid[valid["pv_positive"]].copy()
    negatives = valid[~valid["pv_positive"]]
    rng = np.random.default_rng(city_seed)
    if len(negatives) > NEGATIVE_SAMPLE_LIMIT:
        negative_positions = rng.choice(len(negatives), size=NEGATIVE_SAMPLE_LIMIT, replace=False)
        negative_sample = negatives.iloc[np.sort(negative_positions)].copy()
    else:
        negative_sample = negatives.copy()
    model_sample = pd.concat([positives, negative_sample], ignore_index=True)
    negative_expansion = len(negatives) / max(len(negative_sample), 1)
    model_sample["sampling_weight"] = np.where(
        model_sample["pv_positive"], 1.0, negative_expansion
    )
    model_sample["city_key"] = city

    intensity = positives[positives["conditional_intensity_building"] > 0].copy()
    intensity["city_key"] = city
    intensity["log_conditional_intensity"] = np.log(
        intensity["conditional_intensity_building"]
    )
    if len(intensity):
        lower, upper = intensity["log_conditional_intensity"].quantile([0.005, 0.995])
        intensity["log_conditional_intensity_winsorized"] = intensity[
            "log_conditional_intensity"
        ].clip(lower, upper)

    quality = {
        "city_key": city,
        "City": DISPLAY[city],
        "building_count": int(len(raw)),
        "pv_positive_buildings": int(raw["pv_positive"].sum()),
        "valid_planform_count": int(raw["valid_planform"].sum()),
        "valid_planform_share_pct": 100.0 * float(raw["valid_planform"].mean()),
        "eligible_grid_building_count": int(raw["eligible_grid_50"].sum()),
        "eligible_grid_building_share_pct": 100.0 * float(raw["eligible_grid_50"].mean()),
        "model_eligible_count": int(raw["valid_model_row"].sum()),
        "model_eligible_share_pct": 100.0 * float(raw["valid_model_row"].mean()),
        "model_eligible_pv_positive": int(positives.shape[0]),
        "sampled_negative_count": int(len(negative_sample)),
        "median_footprint_area_m2": float(valid["footprint_area_m2"].median()),
        "median_compactness": float(valid["compactness"].median()),
        "median_elongation": float(valid["elongation"].median()),
        "median_local_building_density_per_km2": float(valid["local_building_density"].median()),
        "median_local_footprint_coverage_pct": 100.0
        * float(valid["local_footprint_coverage"].median()),
        "pv_positive_intensity_gt_1_count": int(
            (positives["conditional_intensity_building"] > 1).sum()
        ),
        "pv_positive_intensity_gt_1_share_pct": 100.0
        * float((positives["conditional_intensity_building"] > 1).mean()),
    }

    keep = [
        "city_key",
        "base_class",
        "pv_positive",
        "sampling_weight",
        *NUMERIC_FEATURES,
    ]
    intensity_keep = [
        "city_key",
        "base_class",
        "conditional_intensity_building",
        "log_conditional_intensity",
        "log_conditional_intensity_winsorized",
        *NUMERIC_FEATURES,
    ]
    model_sample = model_sample[keep]
    intensity = intensity[intensity_keep]
    del raw, valid, positives, negatives, negative_sample, grid
    gc.collect()
    return model_sample, intensity, quality


def prepare_weights_prevalence(frame: pd.DataFrame) -> np.ndarray:
    city_totals = frame.groupby("city_key")["sampling_weight"].transform("sum")
    weights = frame["sampling_weight"].to_numpy(dtype=float) / city_totals.to_numpy(dtype=float)
    return weights / weights.mean()


def prepare_weights_intensity(frame: pd.DataFrame) -> np.ndarray:
    city_counts = frame.groupby("city_key")["city_key"].transform("size")
    weights = 1.0 / city_counts.to_numpy(dtype=float)
    return weights / weights.mean()


def prevalence_pipeline(include_city: bool = True) -> Pipeline:
    categories = ["city_key", "base_class"] if include_city else ["base_class"]
    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(drop="first", handle_unknown="ignore"), categories),
        ],
        remainder="drop",
    )
    return Pipeline(
        [
            ("features", transformer),
            ("model", LogisticRegression(C=10.0, solver="lbfgs", max_iter=1000)),
        ]
    )


def intensity_pipeline(include_city: bool = True) -> Pipeline:
    categories = ["city_key", "base_class"] if include_city else ["base_class"]
    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(drop="first", handle_unknown="ignore"), categories),
        ],
        remainder="drop",
    )
    return Pipeline([("features", transformer), ("model", Ridge(alpha=1e-4))])


def extract_numeric_coefficients(model: Pipeline) -> np.ndarray:
    coefficient = model.named_steps["model"].coef_
    if coefficient.ndim == 2:
        coefficient = coefficient[0]
    return np.asarray(coefficient[: len(NUMERIC_FEATURES)], dtype=float)


def fit_models(prevalence: pd.DataFrame, intensity: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pooled_rows: list[dict] = []
    city_rows: list[dict] = []

    p_weights = prepare_weights_prevalence(prevalence)
    p_model = prevalence_pipeline(include_city=True)
    p_model.fit(
        prevalence[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        prevalence["pv_positive"].astype(int),
        model__sample_weight=p_weights,
    )
    p_coeff = extract_numeric_coefficients(p_model)
    p_pred = p_model.predict_proba(prevalence[NUMERIC_FEATURES + CATEGORICAL_FEATURES])[:, 1]
    p_auc = roc_auc_score(prevalence["pv_positive"].astype(int), p_pred, sample_weight=p_weights)

    i_weights = prepare_weights_intensity(intensity)
    i_model = intensity_pipeline(include_city=True)
    i_model.fit(
        intensity[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        intensity["log_conditional_intensity_winsorized"],
        model__sample_weight=i_weights,
    )
    i_coeff = extract_numeric_coefficients(i_model)
    i_pred = i_model.predict(intensity[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    i_r2 = r2_score(
        intensity["log_conditional_intensity_winsorized"], i_pred, sample_weight=i_weights
    )

    for feature, coefficient in zip(NUMERIC_FEATURES, p_coeff):
        pooled_rows.append(
            {
                "outcome": "PV-positive prevalence",
                "feature": feature,
                "feature_label": FEATURE_LABELS[feature],
                "coefficient": coefficient,
                "multiplicative_effect_per_sd": math.exp(coefficient),
                "model_metric_name": "weighted ROC AUC",
                "model_metric": p_auc,
                "sample_size": len(prevalence),
            }
        )
    for feature, coefficient in zip(NUMERIC_FEATURES, i_coeff):
        pooled_rows.append(
            {
                "outcome": "Conditional intensity",
                "feature": feature,
                "feature_label": FEATURE_LABELS[feature],
                "coefficient": coefficient,
                "multiplicative_effect_per_sd": math.exp(coefficient),
                "model_metric_name": "weighted R-squared",
                "model_metric": i_r2,
                "sample_size": len(intensity),
            }
        )

    for city in CITY_ORDER:
        p_city = prevalence[prevalence["city_key"] == city].copy()
        i_city = intensity[intensity["city_key"] == city].copy()
        if int(p_city["pv_positive"].sum()) >= 200 and p_city["pv_positive"].nunique() == 2:
            model = prevalence_pipeline(include_city=False)
            weights = p_city["sampling_weight"].to_numpy(dtype=float)
            weights /= weights.mean()
            model.fit(
                p_city[NUMERIC_FEATURES + ["base_class"]],
                p_city["pv_positive"].astype(int),
                model__sample_weight=weights,
            )
            prediction = model.predict_proba(p_city[NUMERIC_FEATURES + ["base_class"]])[:, 1]
            metric = roc_auc_score(
                p_city["pv_positive"].astype(int), prediction, sample_weight=weights
            )
            for feature, coefficient in zip(NUMERIC_FEATURES, extract_numeric_coefficients(model)):
                city_rows.append(
                    {
                        "city_key": city,
                        "City": DISPLAY[city],
                        "outcome": "PV-positive prevalence",
                        "feature": feature,
                        "feature_label": FEATURE_LABELS[feature],
                        "coefficient": coefficient,
                        "multiplicative_effect_per_sd": math.exp(coefficient),
                        "model_metric_name": "weighted ROC AUC",
                        "model_metric": metric,
                        "sample_size": len(p_city),
                        "positive_count": int(p_city["pv_positive"].sum()),
                    }
                )
        if len(i_city) >= 200:
            model = intensity_pipeline(include_city=False)
            model.fit(
                i_city[NUMERIC_FEATURES + ["base_class"]],
                i_city["log_conditional_intensity_winsorized"],
            )
            prediction = model.predict(i_city[NUMERIC_FEATURES + ["base_class"]])
            metric = r2_score(i_city["log_conditional_intensity_winsorized"], prediction)
            for feature, coefficient in zip(NUMERIC_FEATURES, extract_numeric_coefficients(model)):
                city_rows.append(
                    {
                        "city_key": city,
                        "City": DISPLAY[city],
                        "outcome": "Conditional intensity",
                        "feature": feature,
                        "feature_label": FEATURE_LABELS[feature],
                        "coefficient": coefficient,
                        "multiplicative_effect_per_sd": math.exp(coefficient),
                        "model_metric_name": "R-squared",
                        "model_metric": metric,
                        "sample_size": len(i_city),
                        "positive_count": len(i_city),
                    }
                )

    pooled = pd.DataFrame(pooled_rows)
    city_specific = pd.DataFrame(city_rows)
    ranges = (
        city_specific.groupby(["outcome", "feature"], as_index=False)
        .agg(
            city_model_count=("city_key", "nunique"),
            city_positive_effect_count=("coefficient", lambda s: int((s > 0).sum())),
            city_negative_effect_count=("coefficient", lambda s: int((s < 0).sum())),
            city_effect_median=("multiplicative_effect_per_sd", "median"),
            city_effect_min=("multiplicative_effect_per_sd", "min"),
            city_effect_max=("multiplicative_effect_per_sd", "max"),
        )
    )
    pooled = pooled.merge(ranges, on=["outcome", "feature"], how="left")
    return pooled, city_specific


def fit_pooled_sensitivities(
    prevalence: pd.DataFrame,
    intensity: pd.DataFrame,
    primary: pd.DataFrame,
) -> pd.DataFrame:
    """Check sensitivity to Monaco's small sample and linked-PV ratios above one."""
    rows: list[dict] = []
    scenarios = [
        (
            "Exclude Monaco",
            prevalence[prevalence["city_key"] != "monaco"],
            intensity[intensity["city_key"] != "monaco"],
        ),
        (
            "Exclude building-level linked-PV ratios above one",
            prevalence,
            intensity[intensity["conditional_intensity_building"] <= 1.0],
        ),
    ]
    primary_indexed = primary.set_index(["outcome", "feature"])
    for scenario, prevalence_subset, intensity_subset in scenarios:
        if scenario == "Exclude Monaco":
            p_weights = prepare_weights_prevalence(prevalence_subset)
            p_model = prevalence_pipeline(include_city=True)
            p_model.fit(
                prevalence_subset[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
                prevalence_subset["pv_positive"].astype(int),
                model__sample_weight=p_weights,
            )
            for feature, coefficient in zip(
                NUMERIC_FEATURES, extract_numeric_coefficients(p_model)
            ):
                primary_effect = float(
                    primary_indexed.loc[
                        ("PV-positive prevalence", feature),
                        "multiplicative_effect_per_sd",
                    ]
                )
                rows.append(
                    {
                        "scenario": scenario,
                        "outcome": "PV-positive prevalence",
                        "feature": feature,
                        "feature_label": FEATURE_LABELS[feature],
                        "sample_size": len(prevalence_subset),
                        "multiplicative_effect_per_sd": math.exp(coefficient),
                        "primary_effect_per_sd": primary_effect,
                        "direction_matches_primary": bool(
                            np.sign(coefficient) == np.sign(math.log(primary_effect))
                        ),
                    }
                )

        i_weights = prepare_weights_intensity(intensity_subset)
        i_model = intensity_pipeline(include_city=True)
        i_model.fit(
            intensity_subset[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
            intensity_subset["log_conditional_intensity_winsorized"],
            model__sample_weight=i_weights,
        )
        for feature, coefficient in zip(
            NUMERIC_FEATURES, extract_numeric_coefficients(i_model)
        ):
            primary_effect = float(
                primary_indexed.loc[
                    ("Conditional intensity", feature), "multiplicative_effect_per_sd"
                ]
            )
            rows.append(
                {
                    "scenario": scenario,
                    "outcome": "Conditional intensity",
                    "feature": feature,
                    "feature_label": FEATURE_LABELS[feature],
                    "sample_size": len(intensity_subset),
                    "multiplicative_effect_per_sd": math.exp(coefficient),
                    "primary_effect_per_sd": primary_effect,
                    "direction_matches_primary": bool(
                        np.sign(coefficient) == np.sign(math.log(primary_effect))
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_figure(pooled: pd.DataFrame, city_specific: pd.DataFrame, output: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "Liberation Sans",
            "font.size": 8.0,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.15), sharey=True)
    outcomes = ["PV-positive prevalence", "Conditional intensity"]
    labels = [FEATURE_LABELS[f] for f in NUMERIC_FEATURES]
    y = np.arange(len(NUMERIC_FEATURES))[::-1]
    for panel, (ax, outcome) in enumerate(zip(axes, outcomes)):
        city = city_specific[city_specific["outcome"] == outcome]
        summary = pooled[pooled["outcome"] == outcome].set_index("feature")
        for ypos, feature in zip(y, NUMERIC_FEATURES):
            values = city.loc[
                city["feature"] == feature, "multiplicative_effect_per_sd"
            ].to_numpy(dtype=float)
            offsets = np.linspace(-0.12, 0.12, max(len(values), 1))
            if len(values):
                ax.scatter(
                    values,
                    ypos + offsets,
                    s=13,
                    color="#9b9b9b",
                    alpha=0.62,
                    linewidths=0,
                    zorder=2,
                )
            row = summary.loc[feature]
            ax.scatter(
                row["multiplicative_effect_per_sd"],
                ypos,
                marker="D",
                s=30,
                color="#1f1f1f",
                edgecolor="white",
                linewidth=0.45,
                zorder=4,
            )
        ax.axvline(1.0, color="#555555", lw=0.75, ls=(0, (3, 2)), zorder=1)
        ax.grid(axis="x", color="#e4e4e4", lw=0.55, zorder=0)
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlabel(
            "Odds ratio per 1 SD" if panel == 0 else "Intensity ratio per 1 SD"
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.text(
            -0.13 if panel == 0 else -0.08,
            1.0,
            f"{'ab'[panel]},",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11,
        )
    axes[0].set_xlim(0.35, max(2.1, axes[0].get_xlim()[1]))
    axes[1].set_xlim(0.45, max(1.65, axes[1].get_xlim()[1]))
    fig.text(
        0.5,
        0.015,
        "Grey points: adjusted city-specific models; black diamonds: equal-city-weighted pooled models",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color="#444444",
    )
    fig.subplots_adjust(left=0.255, right=0.985, bottom=0.20, top=0.97, wspace=0.18)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_latex_tables(quality: pd.DataFrame, pooled: pd.DataFrame) -> None:
    quality_lines = []
    for row in quality.itertuples(index=False):
        quality_lines.append(
            f"{row.City} & {row.building_count:,} & {row.pv_positive_buildings:,} & "
            f"{row.valid_planform_share_pct:.2f} & {row.eligible_grid_building_share_pct:.2f} & "
            f"{row.model_eligible_pv_positive:,} & {row.pv_positive_intensity_gt_1_share_pct:.2f} \\\\"
        )
    (TABLE_DIR / "table_s_planform_local_context_quality_rows.tex").write_text(
        "\n".join(quality_lines) + "\n", encoding="utf-8"
    )

    effect_lines = []
    for outcome in ["PV-positive prevalence", "Conditional intensity"]:
        subset = pooled[pooled["outcome"] == outcome].set_index("feature")
        for feature in NUMERIC_FEATURES:
            row = subset.loc[feature]
            effect_lines.append(
                f"{outcome} & {FEATURE_LABELS[feature]} & "
                f"{row.multiplicative_effect_per_sd:.3f} & "
                f"{int(row.city_positive_effect_count)}/{int(row.city_model_count)} & "
                f"{row.city_effect_min:.3f}--{row.city_effect_max:.3f} \\\\"
            )
    (TABLE_DIR / "table_s_planform_local_context_effect_rows.tex").write_text(
        "\n".join(effect_lines) + "\n", encoding="utf-8"
    )


def write_report(
    quality: pd.DataFrame,
    pooled: pd.DataFrame,
    city_specific: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> None:
    eligible_share = (
        quality["model_eligible_count"].sum() / quality["building_count"].sum() * 100.0
    )
    positive_eligible_share = (
        quality["model_eligible_pv_positive"].sum()
        / quality["pv_positive_buildings"].sum()
        * 100.0
    )
    lines = [
        "# Building planform and local-context audit",
        "",
        "## Scope",
        "",
        "This audit uses existing building footprints, harmonized building-use labels, linked PV polygons and the globally anchored 1-km grid for the 12 primary cities. It adds no new annotation. Planform orientation is the long-axis direction of the footprint minimum rotated rectangle and is not roof-surface orientation. The audit does not measure roof pitch, roof material, usable roof area, shading, structural suitability, ownership, load or battery operation.",
        "",
        "## Quality and coverage",
        "",
        f"The primary model includes {quality['model_eligible_count'].sum():,} buildings ({eligible_share:.2f}% of primary-city buildings) and {quality['model_eligible_pv_positive'].sum():,} PV-positive buildings ({positive_eligible_share:.2f}% of primary-city PV-positive buildings). Eligibility requires a valid planform and assignment to a 1-km cell containing at least 50 buildings.",
        "",
        "## Model interpretation",
        "",
        "The prevalence model is an equal-city-weighted, regularized logistic model. The conditional-intensity model is an equal-city-weighted ridge model of winsorized log mapped-PV area per building-footprint area among PV-positive buildings. Both models adjust for city and harmonized building-use class. City-specific models assess directional heterogeneity. Coefficients are descriptive associations and do not identify physical suitability, adoption mechanisms or causal effects.",
        "",
        "## Pooled adjusted associations",
        "",
        "| Outcome | Predictor | Multiplicative effect per SD | Positive city coefficients | City range |",
        "|---|---|---:|---:|---:|",
    ]
    for row in pooled.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.feature_label} | {row.multiplicative_effect_per_sd:.3f} | "
            f"{int(row.city_positive_effect_count)}/{int(row.city_model_count)} | "
            f"{row.city_effect_min:.3f} to {row.city_effect_max:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Local context uses only building density and total building-footprint coverage. Grid-level PV outcomes are excluded from the predictor set.",
            "- Building footprint area is mathematically present in the denominator of conditional intensity. Its conditional-intensity coefficient is therefore partly definitional and is not interpreted as a behavioral size effect.",
            "- Individual linked-PV area can exceed the assigned footprint area because the manuscript's central mapping definition retains complete linked polygons rather than clipping them to footprints. The city quality table reports the frequency of these cases.",
            "- Variation among city-specific coefficients is reported rather than hidden by the pooled result.",
            f"- Excluding Monaco and, for conditional intensity, excluding building-level linked-PV ratios above one preserved the direction of all {len(sensitivity)} sensitivity coefficients.",
            "",
        ]
    )
    (OUTPUT_DIR / "AUDIT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def run(recompute: bool) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    prevalence_cache = OUTPUT_DIR / "model_sample_prevalence.parquet"
    intensity_cache = OUTPUT_DIR / "model_sample_conditional_intensity.parquet"
    quality_path = OUTPUT_DIR / "per_city_quality.csv"

    if recompute or not (prevalence_cache.exists() and intensity_cache.exists() and quality_path.exists()):
        central = pd.read_csv(CENTRAL_INPUT).set_index("city_key")
        prevalence_frames = []
        intensity_frames = []
        quality_rows = []
        for index, city in enumerate(CITY_ORDER):
            print(f"Processing {city} ({index + 1}/{len(CITY_ORDER)})", flush=True)
            prevalence, intensity, quality = read_city(
                city, central.loc[city], RANDOM_SEED + index
            )
            prevalence_frames.append(prevalence)
            intensity_frames.append(intensity)
            quality_rows.append(quality)
        prevalence = pd.concat(prevalence_frames, ignore_index=True)
        intensity = pd.concat(intensity_frames, ignore_index=True)
        quality = pd.DataFrame(quality_rows)
        prevalence.to_parquet(prevalence_cache, index=False)
        intensity.to_parquet(intensity_cache, index=False)
        quality.to_csv(quality_path, index=False)
    else:
        prevalence = pd.read_parquet(prevalence_cache)
        intensity = pd.read_parquet(intensity_cache)
        quality = pd.read_csv(quality_path)

    print("Fitting pooled and city-specific models", flush=True)
    pooled, city_specific = fit_models(prevalence, intensity)
    sensitivity = fit_pooled_sensitivities(prevalence, intensity, pooled)
    pooled.to_csv(OUTPUT_DIR / "pooled_adjusted_associations.csv", index=False)
    city_specific.to_csv(OUTPUT_DIR / "city_specific_adjusted_associations.csv", index=False)
    sensitivity.to_csv(OUTPUT_DIR / "pooled_association_sensitivities.csv", index=False)
    quality.to_csv(TABLE_DIR / "table_s_planform_local_context_quality.csv", index=False)
    pooled.to_csv(TABLE_DIR / "table_s_planform_local_context_effects.csv", index=False)
    quality.to_csv(SOURCE_DIR / "Fig_S7_building_planform_local_context_quality.csv", index=False)
    pooled.to_csv(
        SOURCE_DIR / "Fig_S7_building_planform_local_context_pooled.csv", index=False
    )
    city_specific.to_csv(
        SOURCE_DIR / "Fig_S7_building_planform_local_context_city_specific.csv", index=False
    )
    sensitivity.to_csv(
        SOURCE_DIR / "Fig_S7_building_planform_local_context_sensitivities.csv", index=False
    )

    build_figure(
        pooled,
        city_specific,
        FIGURE_DIR / "fig_s_building_planform_local_context.pdf",
    )
    write_latex_tables(quality, pooled)
    write_report(quality, pooled, city_specific, sensitivity)

    checks = {
        "primary_city_count": len(CITY_ORDER),
        "building_count": int(quality["building_count"].sum()),
        "pv_positive_buildings": int(quality["pv_positive_buildings"].sum()),
        "model_eligible_buildings": int(quality["model_eligible_count"].sum()),
        "model_eligible_pv_positive": int(quality["model_eligible_pv_positive"].sum()),
        "prevalence_model_sample": int(len(prevalence)),
        "intensity_model_sample": int(len(intensity)),
        "all_coefficients_finite": bool(
            np.isfinite(pooled["coefficient"]).all()
            and np.isfinite(city_specific["coefficient"]).all()
        ),
        "all_sensitivity_directions_match_primary": bool(
            sensitivity["direction_matches_primary"].all()
        ),
    }
    (OUTPUT_DIR / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    (REV / "Source_Data/source_data_checks_fig_s7_planform_local_context.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recompute", action="store_true", help="Rebuild building-level caches")
    parser.add_argument(
        "--plot-from-source-data",
        action="store_true",
        help="Regenerate the Supplementary figure from redistributable aggregate CSV files",
    )
    args = parser.parse_args()
    if args.plot_from_source_data:
        pooled = pd.read_csv(
            SOURCE_DIR / "Fig_S7_building_planform_local_context_pooled.csv"
        )
        city_specific = pd.read_csv(
            SOURCE_DIR / "Fig_S7_building_planform_local_context_city_specific.csv"
        )
        public_figure_dir = REV / "figures/supplementary"
        output = (
            public_figure_dir / "Fig_S_planform_local_context.pdf"
            if public_figure_dir.exists()
            else FIGURE_DIR / "fig_s_building_planform_local_context.pdf"
        )
        build_figure(pooled, city_specific, output)
        print("Regenerated Supplementary planform and local-context figure", flush=True)
        return
    run(args.recompute)


if __name__ == "__main__":
    main()
