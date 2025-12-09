import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Methane Tracker", layout="wide")


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load and clean methane data from the Excel file."""
    data_path = Path(__file__).parent / "METHANE TRACKER.xlsx"
    df = pd.read_excel(data_path)
    df.columns = [col.strip() for col in df.columns]
    emission_col = "EMISSION (KT)"
    df[emission_col] = pd.to_numeric(df[emission_col], errors="coerce")
    return df


def build_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return the filtered dataframe."""
    emission_col = "EMISSION (KT)"
    working = df.copy()

    st.sidebar.header("Filters")

    region_opts = sorted(working["REGION"].dropna().unique())
    selected_regions = st.sidebar.multiselect("Region", region_opts)
    if selected_regions:
        working = working[working["REGION"].isin(selected_regions)]

    country_opts = sorted(working["COUNTRY"].dropna().unique())
    selected_countries = st.sidebar.multiselect("Country", country_opts)
    if selected_countries:
        working = working[working["COUNTRY"].isin(selected_countries)]

    source_opts = sorted(working["SOURCES"].dropna().unique())
    selected_sources = st.sidebar.multiselect("Source", source_opts)
    if selected_sources:
        working = working[working["SOURCES"].isin(selected_sources)]

    segment_opts = sorted(working["SEGMENT"].dropna().unique())
    selected_segments = st.sidebar.multiselect("Segment", segment_opts)
    if selected_segments:
        working = working[working["SEGMENT"].isin(selected_segments)]

    reason_opts = sorted(working["REASON"].dropna().unique())
    selected_reasons = st.sidebar.multiselect("Reason", reason_opts)
    if selected_reasons:
        working = working[working["REASON"].isin(selected_reasons)]

    return working


def plot_map(df: pd.DataFrame, global_max: float | None) -> None:
    """Render a choropleth map showing emissions by country."""
    emission_col = "EMISSION (KT)"
    map_data = (
        df.groupby(["COUNTRY", "REGION"], as_index=False)[emission_col]
        .sum()
        .dropna(subset=["COUNTRY"])
    )

    if map_data.empty:
        st.info("No data available for the current filters.")
        return

    fig = px.choropleth(
        map_data,
        locations="COUNTRY",
        locationmode="country names",
        color=emission_col,
        hover_name="COUNTRY",
        hover_data={"REGION": True, emission_col: ":,.0f"},
        color_continuous_scale="YlOrRd",
        range_color=(0, global_max) if pd.notna(global_max) else None,
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        coloraxis_colorbar_title="KT",
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_sunburst(df: pd.DataFrame) -> None:
    """Render a sunburst with SOURCES as inner ring and SEGMENT (Energy) or COUNTRY as outer ring."""
    if df.empty:
        st.info("No data available for the current filters.")
        return

    emission_col = "EMISSION (KT)"
    working = df.copy()
    working["outer"] = working.apply(
        lambda r: r["SEGMENT"]
        if isinstance(r["SOURCES"], str)
        and r["SOURCES"].strip().lower() == "energy"
        and pd.notna(r["SEGMENT"])
        else r["COUNTRY"],
        axis=1,
    )

    sun_data = (
        working.dropna(subset=["SOURCES", "outer", emission_col])
        .loc[
            lambda d: ~d["outer"].str.strip().str.lower().isin(["world", "total"])
        ]
        .groupby(["SOURCES", "outer"], as_index=False)[emission_col]
        .sum()
    )

    if sun_data.empty:
        st.info("No data available for the current filters.")
        return

    fig = px.sunburst(
        sun_data,
        path=["SOURCES", "outer"],
        values=emission_col,
        color="SOURCES",
        hover_data={emission_col: ":,.0f"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=500)
    st.plotly_chart(fig, use_container_width=True)


def plot_top_countries_bar(df: pd.DataFrame) -> None:
    """Bar chart for top 10 countries by emission, excluding world/total placeholders."""
    if df.empty:
        st.info("No data available for the current filters.")
        return

    emission_col = "EMISSION (KT)"
    bars = (
        df.dropna(subset=["COUNTRY", emission_col])
        .loc[
            lambda d: ~d["COUNTRY"].str.strip().str.lower().isin(["world", "total"])
        ]
        .groupby("COUNTRY", as_index=False)[emission_col]
        .sum()
        .sort_values(emission_col, ascending=False)
        .head(10)
    )

    if bars.empty:
        st.info("No data available for the current filters.")
        return

    fig = px.bar(
        bars,
        x="COUNTRY",
        y=emission_col,
        text_auto=".3s",
        title="Top 10 Countries by Emissions",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=420)
    st.plotly_chart(fig, use_container_width=True)


def plot_region_source_stacked(df: pd.DataFrame) -> None:
    """Stacked bar chart: Region on x-axis, stacked by Sources."""
    if df.empty:
        st.info("No data available for the current filters.")
        return

    emission_col = "EMISSION (KT)"
    stacked = (
        df.dropna(subset=["REGION", "SOURCES", emission_col])
        .loc[
            lambda d: ~d["COUNTRY"].str.strip().str.lower().isin(["world", "total"])
        ]
        .groupby(["REGION", "SOURCES"], as_index=False)[emission_col]
        .sum()
    )

    if stacked.empty:
        st.info("No data available for the current filters.")
        return

    fig = px.bar(
        stacked,
        x="REGION",
        y=emission_col,
        color="SOURCES",
        text_auto=".3s",
        title="Regional Emissions by Source",
    )
    fig.update_layout(barmode="stack", margin=dict(l=0, r=0, t=30, b=0), height=450)
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("Global Methane Tracker")
    st.caption("Explore methane emissions by country, region, source, segment, and reason.")

    df = load_data()
    global_max = df["EMISSION (KT)"].max(skipna=True)
    filtered = build_filters(df)
    logo_path = Path(__file__).parent / "logo.png"

    tab_emission, tab_glossary, tab_dashboard = st.tabs(
        ["Methane Emission", "Emission Glossary", "Dashboard"]
    )

    with tab_emission:
        #st.subheader("Methane Emission")
        md_path = Path(__file__).parent / "emission.md"
        if md_path.exists():
            md_text = md_path.read_text(encoding="utf-8")
            # Remove embedded image line (we render it explicitly below)
            lines = md_text.splitlines()
            cleaned_lines = [
                line
                for line in lines
                if "licensed-image.jpeg" not in line and "licenced-image.jpeg" not in line
            ]
            image_path = None
            for candidate in ("licensed-image.jpeg", "licenced-image.jpeg"):
                candidate_path = Path(__file__).parent / candidate
                if candidate_path.exists():
                    image_path = candidate_path
                    break
            if image_path:
                st.image(image_path, use_container_width=True)
            st.markdown("\n".join(cleaned_lines))
        else:
            st.info("emission.md not found.")

    with tab_dashboard:
        st.subheader("Global View")
        plot_map(filtered, global_max)

        st.subheader("Composition")
        plot_sunburst(filtered)

        st.subheader("Top 10 Countries")
        plot_top_countries_bar(filtered)

        st.subheader("Regional Profile by Source")
        plot_region_source_stacked(filtered)

        st.subheader("Detailed Records")
        if filtered.empty:
            st.info("No rows match the current filters.")
        else:
            st.dataframe(
                filtered.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

    with tab_glossary:
        glossary_path = Path(__file__).parent / "glossary.md"
        if glossary_path.exists():
            st.markdown(
                glossary_path.read_text(encoding="utf-8"), unsafe_allow_html=True
            )
        else:
            st.info("glossary.md not found.")

    # Fixed logo in the bottom-right corner
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        st.markdown(
            """
            <style>
            .fixed-logo {
                position: fixed;
                right: 16px;
                bottom: 16px;
                width: 120px;
                z-index: 9999;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<img class="fixed-logo" src="data:image/png;base64,{logo_b64}" />',
            unsafe_allow_html=True,
        )
    else:
        st.info("logo.png not found; place it alongside streamlit_app.py to show the logo.")


if __name__ == "__main__":
    main()
