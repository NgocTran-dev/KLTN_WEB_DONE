import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.ui import apply_base_style
from utils.geocode import geocode_many
from utils.io import load_data

st.set_page_config(page_title="Dashboard", layout="wide")
apply_base_style()

GOV = "Gov Price 2026 Corrected (million VND/m²)"
MARKET = "Market Reference Unit Price (median, million VND/m²)"
GAP = "Price Gap Corrected"
RISK = "Risk Score"
FAKE = "Độ tin cậy tin ảo (%)"

st.title("Dashboard")
st.caption("Tổng hợp Price Gap và Risk Score theo khu vực, kèm bản đồ heatmap.")

# --- Load data ---
df, _, _ = load_data(frontage_only=True)

# --- Filters ---
left, right = st.columns([1.2, 1.8])
with left:
    districts = st.multiselect(
        "Chọn quận",
        options=sorted(df["District"].dropna().unique().tolist()),
        default=sorted(df["District"].dropna().unique().tolist()),
    )

    mode = st.radio(
        "Chế độ bản đồ",
        options=["Theo tuyến đường (gọn)", "Theo từng tin (dày)"],
        index=0
    )

    metric = st.selectbox(
        "Heatmap theo chỉ số",
        options=["Price Gap", "Risk Score", "Mật độ tin"],
        index=0,
    )

    heat_radius = st.slider("Bán kính heatmap (px)", min_value=10, max_value=150, value=60, step=5)
    point_radius = st.slider("Bán kính điểm (m)", min_value=20, max_value=300, value=90, step=10)

    refresh_coords = st.checkbox(
        "Cải thiện tọa độ theo OSM/Nominatim (chỉ áp dụng 'Theo tuyến đường')",
        value=False,
    )
    st.markdown("<div class='muted'>Tuỳ chọn này có thể mất thời gian ở lần chạy đầu.</div>", unsafe_allow_html=True)
    geocode_limit = st.slider(
        "Giới hạn số tuyến geocode lại",
        min_value=10,
        max_value=120,
        value=40,
        step=10,
        disabled=not refresh_coords,
    )

with right:
    st.subheader("Thống kê nhanh")
    if len(districts) == 0:
        st.warning("Vui lòng chọn ít nhất 1 quận.")
        st.stop()

    dff = df[df["District"].isin(districts)].copy()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Số tin", f"{len(dff):,}")
    with c2:
        st.metric("Price Gap (median)", f"{np.nanmedian(dff[GAP]):.3f}×")
    with c3:
        st.metric("Risk (mean)", f"{np.nanmean(dff[RISK]):.3f}")
    with c4:
        st.metric("S_fake (mean)", f"{np.nanmean(dff[FAKE]):.1f}%")

st.divider()

# --- Charts ---
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("Phân bố Price Gap")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    for d in sorted(dff["District"].dropna().unique().tolist()):
        vals = dff.loc[dff["District"] == d, GAP].dropna().values
        if len(vals) == 0:
            continue
        ax.hist(vals, bins=30, alpha=0.55, label=f"Q{int(d)}")

    ax.set_xlabel("Price Gap")
    ax.set_ylabel("Số lượng")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

with chart2:
    st.subheader("Price Gap theo quận (boxplot)")
    import matplotlib.pyplot as plt

    # đảm bảo có dữ liệu hợp lệ để vẽ
    dplot = dff[["District", GAP]].dropna()

    fig, ax = plt.subplots()
    dplot.boxplot(column=GAP, by="District", grid=False, ax=ax)

    fig.suptitle("")  # bỏ title mặc định "Boxplot grouped by..."
    ax.set_title("")
    ax.set_xlabel("Quận")
    ax.set_ylabel("Price Gap")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

# --- Top streets (dynamic) ---
st.subheader("Top tuyến đường theo Price Gap (median, n≥10)")

street_agg = (
    dff.groupby(["District", "Ward", "Street"], dropna=True)
    .agg(
        Listings=("Street", "size"),
        Latitude=("Latitude", "median"),
        Longitude=("Longitude", "median"),
        Median_Gov=(GOV, "median"),
        Median_Market=(MARKET, "median"),
        Median_Gap=(GAP, "median"),
        Mean_Risk=(RISK, "mean"),
        Mean_Fake=(FAKE, "mean"),
    )
    .reset_index()
)

street_top = street_agg[street_agg["Listings"] >= 10].sort_values("Median_Gap", ascending=False).head(15)

st.dataframe(
    street_top[["District", "Ward", "Street", "Listings", "Median_Market", "Median_Gov", "Median_Gap", "Mean_Risk"]],
    use_container_width=True,
)

st.divider()

# --- Map prep ---
st.subheader("Bản đồ (Heatmap + điểm)")

if mode.startswith("Theo tuyến"):
    points = street_agg.copy()
    points["listings"] = points["Listings"].astype(float)
    points["metric_gap"] = points["Median_Gap"].astype(float)
    points["metric_risk"] = points["Mean_Risk"].astype(float)

    if refresh_coords:
        # Identify coordinates that are shared by many streets (often caused by coarse geocoding)
        coord_counts = (
            points.groupby(["Latitude", "Longitude"], dropna=True)
            .size()
            .reset_index(name="cnt")
            .sort_values("cnt", ascending=False)
        )
        dup_coords = coord_counts[coord_counts["cnt"] >= 3].head(geocode_limit)

        if len(dup_coords) > 0:
            # Build geocode queries for affected streets
            points = points.merge(
                dup_coords[["Latitude", "Longitude"]],
                on=["Latitude", "Longitude"],
                how="left",
                indicator=True,
            )
            needs_fix = points["_merge"].eq("both")
            points.loc[needs_fix, "geo_query"] = (
                points.loc[needs_fix, "Street"].astype(str)
                + ", "
                + points.loc[needs_fix, "Ward"].astype(str)
                + ", Quận "
                + points.loc[needs_fix, "District"].astype(int).astype(str)
                + ", Thành phố Hồ Chí Minh, Việt Nam"
            )

            with st.spinner("Đang geocode lại một số tuyến theo Nominatim..."):
                q_list = points.loc[needs_fix, "geo_query"].dropna().unique().tolist()
                geo_map = geocode_many(q_list)

            def _map_lat(q):
                return geo_map.get(q, (np.nan, np.nan))[0]

            def _map_lon(q):
                return geo_map.get(q, (np.nan, np.nan))[1]

            points.loc[needs_fix, "Latitude"] = points.loc[needs_fix, "geo_query"].map(_map_lat)
            points.loc[needs_fix, "Longitude"] = points.loc[needs_fix, "geo_query"].map(_map_lon)

        else:
            st.info("Không phát hiện cụm tọa độ trùng nhiều để geocode lại.")

else:
    points = dff.copy()
    points["listings"] = 1.0
    points["metric_gap"] = points[GAP].astype(float)
    points["metric_risk"] = points[RISK].astype(float)

    if refresh_coords:
        st.info("Tùy chọn geocode lại chỉ áp dụng cho chế độ 'Theo tuyến đường'.")

# Clean coords
points["Latitude"] = pd.to_numeric(points["Latitude"], errors="coerce")
points["Longitude"] = pd.to_numeric(points["Longitude"], errors="coerce")
points = points.dropna(subset=["Latitude", "Longitude"]).copy()

if len(points) == 0:
    st.warning("Không có tọa độ hợp lệ để vẽ bản đồ.")
    st.stop()

# Choose heatmap weight + point color metric
if metric == "Price Gap":
    weight_col = "metric_gap"
    color_vals = points["metric_gap"]
elif metric == "Risk Score":
    weight_col = "metric_risk"
    color_vals = points["metric_risk"]
else:
    weight_col = "listings"
    color_vals = points["listings"]

# Normalize for colors
t = (color_vals - color_vals.min()) / (color_vals.max() - color_vals.min() + 1e-9)
points["color"] = [[int(255 * tt), int(80), int(255 * (1 - tt)), 160] for tt in t.fillna(0).clip(0, 1).tolist()]

# View state
center_lat = float(points["Latitude"].mean())
center_lon = float(points["Longitude"].mean())
zoom_default = 14.2 if len(districts) == 1 else 13.6

map_style = st.selectbox(
    "Map style",
    options=[
        "Carto Positron (light)",
        "Carto Dark Matter (dark)",
        "Carto Voyager (default)",
    ],
    index=0,
)

style_map = {
    "Carto Positron (light)": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Carto Dark Matter (dark)": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Carto Voyager (default)": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
}

view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom_default, pitch=30)

layers = [
    pdk.Layer(
        "HeatmapLayer",
        data=points,
        get_position="[Longitude, Latitude]",
        get_weight=weight_col,
        radius_pixels=heat_radius,
    ),
    pdk.Layer(
        "ScatterplotLayer",
        data=points,
        get_position="[Longitude, Latitude]",
        get_radius=point_radius,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    ),
]

tooltip = {
    "html": "<b>Quận:</b> {District} <br/> <b>Phường:</b> {Ward} <br/> <b>Đường:</b> {Street} <br/> <b>Price Gap:</b> {Median_Gap} <br/> <b>Risk:</b> {Mean_Risk} <br/> <b>Số tin:</b> {Listings}",
    "style": {"backgroundColor": "white", "color": "black"},
}

if not mode.startswith("Theo tuyến"):
    tooltip["html"] = (
        "<b>Quận:</b> {District} <br/> <b>Phường:</b> {Ward} <br/> <b>Đường:</b> {Street} "
        "<br/> <b>Price Gap:</b> {metric_gap} <br/> <b>Risk:</b> {metric_risk}"
    )

r = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style=style_map.get(map_style),
    tooltip=tooltip,
)

st.pydeck_chart(r, use_container_width=True)

st.caption(
    "Nếu điểm vẫn bị dồn: thử giảm bán kính heatmap/điểm hoặc chuyển sang theo tuyến đường. "
    "Bạn cũng có thể bật 'Cải thiện tọa độ' để geocode lại các cụm bị trùng nhiều."
)
