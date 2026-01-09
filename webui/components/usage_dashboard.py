import streamlit as st
import duckdb
import pandas as pd
from core.paths import PARQUET_DIR


def usage_dashboard():
    st.header("Usage")
    st.caption("Usage analytics derived from gateway logs.")

    if not PARQUET_DIR.exists():
        st.warning("No usage data found")
        return

    con = duckdb.connect()
    try:
        df = con.execute(
            "SELECT * FROM read_parquet(?)",
            [str(PARQUET_DIR / "*.parquet")],
        ).df()
    except Exception as exc:
        st.error(f"Failed to read usage data: {exc}")
        return

    if "timestamp" not in df.columns:
        st.warning("Usage data missing timestamp column.")
        return

    df["ts"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce", utc=True)
    df = df.dropna(subset=["ts"]).copy()
    if df.empty:
        st.info("No usage records in the selected files.")
        return

    df["status_code"] = pd.to_numeric(df.get("status_code"), errors="coerce")
    df["total_tokens"] = pd.to_numeric(df.get("total_tokens"), errors="coerce").fillna(
        0
    )
    df["duration_ms"] = pd.to_numeric(df.get("duration_ms"), errors="coerce")

    st.subheader("Filters")
    min_date = df["ts"].min().date()
    max_date = df["ts"].max().date()
    date_range = st.date_input(
        "Date range (UTC)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    provider_filter = st.multiselect(
        "Provider",
        sorted(df.get("provider", pd.Series(dtype=str)).dropna().unique().tolist()),
    )
    owner_filter = st.multiselect(
        "Owner",
        sorted(df.get("owner", pd.Series(dtype=str)).dropna().unique().tolist()),
    )
    model_filter = st.multiselect(
        "Model",
        sorted(df.get("model", pd.Series(dtype=str)).dropna().unique().tolist()),
    )
    status_filter = st.multiselect(
        "Status code",
        sorted(df.get("status_code", pd.Series(dtype=int)).dropna().unique().tolist()),
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["ts"].dt.date >= start) & (df["ts"].dt.date <= end)]
    else:
        df = df[df["ts"].dt.date == date_range]

    if provider_filter and "provider" in df.columns:
        df = df[df["provider"].isin(provider_filter)]
    if owner_filter and "owner" in df.columns:
        df = df[df["owner"].isin(owner_filter)]
    if model_filter and "model" in df.columns:
        df = df[df["model"].isin(model_filter)]
    if status_filter and "status_code" in df.columns:
        df = df[df["status_code"].isin(status_filter)]

    if df.empty:
        st.info("No usage records match the selected filters.")
        return

    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Requests", len(df))
    col2.metric("Total tokens", int(df["total_tokens"].sum()))
    if df["duration_ms"].notna().any():
        col3.metric("Avg latency (ms)", int(df["duration_ms"].mean()))
    else:
        col3.metric("Avg latency (ms)", "n/a")
    if df["status_code"].notna().any():
        col4.metric("Error rate", f"{(df['status_code'] >= 400).mean():.1%}")
    else:
        col4.metric("Error rate", "n/a")

    st.subheader("Requests over time")
    df_ts = df.set_index("ts").resample("1H").size()
    st.line_chart(df_ts)

    st.subheader("Raw events")
    st.dataframe(df.sort_values("ts", ascending=False))
