import hashlib
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from astroquery.gaia import Gaia
import warnings

warnings.filterwarnings('ignore')

Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"

CACHE_DIR = "gaia_cache"

SPECTRAL_CLASSES = [
    ("O", (-np.inf, -0.30),   "#9BB0FF"),
    ("B", (-0.30,    0.00),   "#AABFFF"),
    ("A", ( 0.00,    0.30),   "#F8F7FF"),
    ("F", ( 0.30,    0.60),   "#FFF4EA"),
    ("G", ( 0.60,    0.90),   "#FFDF80"),
    ("K", ( 0.90,    1.50),   "#FFAA55"),
    ("M", ( 1.50,    np.inf), "#FF4500"),
]

NUM_STARS = 5000


def _cache_key(columns: list[str], filters: dict, num_stars: int) -> str:
    params = {
        "columns": sorted(columns),
        "filters": filters,
        "num_stars": num_stars,
    }
    digest = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:10]
    return os.path.join(CACHE_DIR, f"gaia_{digest}.parquet")


def _load_cache(path: str) -> pd.DataFrame | None:
    if os.path.exists(path):
        print(f"Loading cached results from {path}")
        return pd.read_parquet(path)
    return None


def _save_cache(df: pd.DataFrame, path: str) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Results cached to {path}")


def fetch_stars(columns: list[str] = None,
                filters: dict = None,
                num_stars: int = NUM_STARS) -> pd.DataFrame:
    if columns is None:
        columns = ["designation", "ra", "dec", "parallax", "bp_rp"]
    if filters is None:
        filters = {"parallax": 0.1, "parallax_over_error": 5}

    cache_path = _cache_key(columns, filters, num_stars)
    cached = _load_cache(cache_path)
    if cached is not None and len(cached) >= num_stars:
        return cached.head(num_stars)

    print(f"Cache miss - querying Gaia DR3 for {num_stars} stars...")

    col_str = ", ".join(columns)
    where_str = " AND ".join(f"{col} > {val}" for col, val, in filters.items())

    job = Gaia.launch_job_async(
        f"""
        select top {num_stars}
            {col_str}
        from gaiadr3.gaia_source
        where {where_str}
        order by random_index
        """
    )

    results = job.get_results()
    df = results.to_pandas()
    _save_cache(df, cache_path)
    return df


def classify_spectral_class(bp_rp: float) -> tuple[str, str]:
    if bp_rp is None or np.isnan(bp_rp):
        return "Unknown", "#888888"

    for label, (lo, hi), colour in SPECTRAL_CLASSES:
        if lo <= bp_rp < hi:
            return label, colour

    return "Unknown", "#888888"


def query_gaia():
    df = fetch_stars(num_stars=NUM_STARS)
    df = df.dropna(subset=["bp_rp"])

    ra_rad = np.radians(df['ra'].to_numpy())
    dec_rad = np.radians(df['dec'].to_numpy())
    distance = 1.0 / df['parallax'].to_numpy()

    x = distance * np.cos(dec_rad) * np.cos(ra_rad)
    y = distance * np.cos(dec_rad) * np.sin(ra_rad)
    z = distance * np.sin(dec_rad)

    df['x'] = x
    df['y'] = y
    df['z'] = z
    df[['spectral_class', 'colour']] = df['bp_rp'].apply(
        lambda v: pd.Series(classify_spectral_class(v))
    )

    sun = dict(x=0.0, y=0.0, z=0.0)
    sgr_ra = np.radians(266.4168)
    sgr_dec = np.radians(-29.0078)
    sgr_d = 8.178
    sgr_a = dict(
        x = sgr_d * np.cos(sgr_dec) * np.cos(sgr_ra),
        y = sgr_d * np.cos(sgr_dec) * np.sin(sgr_ra),
        z = sgr_d * np.sin(sgr_dec),
    )

    traces = []
    for label, _, colour in SPECTRAL_CLASSES:
        subset = df[df['spectral_class'] == label]
        if subset.empty:
            continue
        traces.append(go.Scatter3d(
            x=subset['x'], y=subset['y'], z=subset['z'],
            mode='markers',
            name=f"Class {label}",
            marker=dict(
                size=2,
                color=colour,
                opacity=0.85,
                line=dict(width=0),
            ),
            customdata=subset[['designation']].to_numpy(),
            hovertemplate=(
                    f"<b>%{{customdata[0]}}</b><br>"
                    "<b>Class " + label + "</b><br>"
                    "X: %{x:.2f} kpc<br>"
                    "Y: %{y:.2f} kpc<br>"
                    "Z: %{z:.2f} kpc<br>"
                    "<extra></extra>"
            ),
        ))

    # sun
    traces.append(go.Scatter3d(
        x=[sun['x']], y=[sun['y']], z=[sun['z']],
        mode='markers+text',
        name='Sun',
        text=['Sun'],
        textposition='top center',
        textfont=dict(color='yellow', size=11),
        marker=dict(size=6, color='yellow', symbol='circle',
                    line=dict(color='white', width=1)),
        hovertemplate="<b>Sun</b><br>X: 0.00 kpc<br>Y: 0.00 kpc<br>Z: 0.00 kpc<extra></extra>",
    ))

    # Sagittarius A*
    traces.append(go.Scatter3d(
        x=[sgr_a['x']], y=[sgr_a['y']], z=[sgr_a['z']],
        mode='markers+text',
        name='Sagittarius A*',
        text=['Sgr A*'],
        textposition='top center',
        textfont=dict(color='#ff6ec7', size=11),
        marker=dict(size=6, color='#ff6ec7', symbol='circle',
                    line=dict(color='white', width=1)),
        hovertemplate=(
            "<b>Sagittarius A*</b><br>"
            f"X: {sgr_a['x']:.2f} kpc<br>"
            f"Y: {sgr_a['y']:.2f} kpc<br>"
            f"Z: {sgr_a['z']:.2f} kpc<extra></extra>"
        ),
    ))

    # Line from Sun to Sagittarius A*
    traces.append(go.Scatter3d(
        x=[sun['x'], sgr_a['x']],
        y=[sun['y'], sgr_a['y']],
        z=[sun['z'], sgr_a['z']],
        mode='lines',
        name='Sun → Sgr A*',
        line=dict(color='white', width=2, dash='dash'),
        hoverinfo='skip',
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text="Milky Way Stars — Gaia DR3", font=dict(color="white", size=18)),
        paper_bgcolor="black",
        scene=dict(
            bgcolor="black",
            xaxis=dict(title="X (kpc)", color="white", gridcolor="#333333", showbackground=False),
            yaxis=dict(title="Y (kpc)", color="white", gridcolor="#333333", showbackground=False),
            zaxis=dict(title="Z (kpc)", color="white", gridcolor="#333333", showbackground=False),
        ),
        legend=dict(
            font=dict(color="white"),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="#444444",
            borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    output_path = "output/milky_way.html"
    os.makedirs("output", exist_ok=True)
    fig.write_html(output_path)
    print(f"Plot saved to {output_path}")


if __name__ == "__main__":
    query_gaia()
