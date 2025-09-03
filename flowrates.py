import streamlit as st
import pandas as pd

st.set_page_config(page_title="Flowrate Unit Converter", page_icon="💧", layout="centered")

st.title("💧 Flowrate Unit Converter")
st.caption("Convert between L/min, mL/min, µL/min, nL/min, L/h, mL/h, and µL/h — with batch mode & CSV export.")

# --- Unit definitions (base = L/min) ---
UNITS = {
    # per minute
    "L/min":   {"to_base": lambda x: x,             "from_base": lambda x: x},
    "mL/min":  {"to_base": lambda x: x / 1_000.0,   "from_base": lambda x: x * 1_000.0},
    "µL/min":  {"to_base": lambda x: x * 1e-6,      "from_base": lambda x: x / 1e-6},
    "uL/min":  {"to_base": lambda x: x * 1e-6,      "from_base": lambda x: x / 1e-6},  # alias
    "nL/min":  {"to_base": lambda x: x * 1e-9,      "from_base": lambda x: x / 1e-9},

    # per hour
    "L/h":     {"to_base": lambda x: x / 60.0,      "from_base": lambda x: x * 60.0},
    "mL/h":    {"to_base": lambda x: (x / 1_000.0) / 60.0, "from_base": lambda x: x * 60.0 * 1_000.0},
    "µL/h":    {"to_base": lambda x: (x * 1e-6) / 60.0,    "from_base": lambda x: x * 60.0 / 1e-6},
    "uL/h":    {"to_base": lambda x: (x * 1e-6) / 60.0,    "from_base": lambda x: x * 60.0 / 1e-6},  # alias
}

# Preferred display order
DISPLAY_UNITS = ["L/min", "mL/min", "µL/min", "nL/min", "L/h", "mL/h", "µL/h"]

# Normalize aliases to display symbols
ALIAS = {"uL/min": "µL/min", "uL/h": "µL/h"}

# --- Sidebar options ---
st.sidebar.header("Options")
decimals = st.sidebar.slider("Decimal places", min_value=0, max_value=8, value=3, step=1)
sci_for_large = st.sidebar.checkbox("Use scientific notation for large/small values", value=True)
thresh = st.sidebar.number_input("Sci-notation threshold (|x| < 1e- or > 1e+)", min_value=1, max_value=12, value=6)

def fmt(x: float) -> str:
    if pd.isna(x):
        return ""
    if sci_for_large and (abs(x) > 10**thresh or (x != 0 and abs(x) < 10**(-thresh))):
        return f"{x:.{decimals}e}"
    return f"{x:.{decimals}f}"

# --- Single value converter ---
st.subheader("Single Value Conversion")

col1, col2 = st.columns(2)
with col1:
    value = st.number_input("Value", min_value=0.0, value=1.0, step=1.0, format="%.10f")
with col2:
    in_unit = st.selectbox("From unit", DISPLAY_UNITS + ["uL/min", "uL/h"], index=0)  # default L/min

display_in_unit = ALIAS.get(in_unit, in_unit)
base = UNITS[in_unit]["to_base"](value)

rows = []
for out_unit in DISPLAY_UNITS:
    converted = UNITS[out_unit]["from_base"](base)
    rows.append({"Unit": out_unit, "Value": converted, "Formatted": fmt(converted)})

df_single = pd.DataFrame(rows, columns=["Unit", "Value", "Formatted"])
st.markdown(f"**Input:** {fmt(value)} {display_in_unit}")
st.table(df_single[["Unit", "Formatted"]].set_index("Unit"))

# --- Batch converter ---
st.subheader("Batch Conversion (optional)")
st.caption("Paste one value per line (numbers only). Choose the input unit and get all outputs.")

batch_col1, batch_col2 = st.columns([2, 1])
with batch_col1:
    raw = st.text_area("Values (one per line)", value="", height=160, placeholder="e.g.\n0.5\n12\n2500.75")
with batch_col2:
    batch_unit = st.selectbox("Batch input unit", DISPLAY_UNITS + ["uL/min", "uL/h"], index=2)  # default µL/min

if raw.strip():
    values = []
    for i, line in enumerate(raw.splitlines(), start=1):
        s = line.strip().replace(",", "")  # allow "1,000"
        if s == "":
            continue
        try:
            values.append(float(s))
        except ValueError:
            st.warning(f"Line {i} is not a number: {line!r} — skipping it.")

    if values:
        data = {"Input": values, "Input Unit": [ALIAS.get(batch_unit, batch_unit)] * len(values)}
        base_vals = [UNITS[batch_unit]["to_base"](v) for v in values]
        for out_unit in DISPLAY_UNITS:
            conv = [UNITS[out_unit]["from_base"](b) for b in base_vals]
            data[out_unit] = conv
            data[f"{out_unit} (fmt)"] = [fmt(x) for x in conv]

        df_batch = pd.DataFrame(data)
        show_cols = ["Input", "Input Unit"] + [f"{u} (fmt)" for u in DISPLAY_UNITS]
        st.dataframe(df_batch[show_cols], use_container_width=True)

        csv = df_batch.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV (raw numeric)",
            data=csv,
            file_name="flowrate_conversions.csv",
            mime="text/csv",
        )
    else:
        st.info("No valid numeric lines found.")

# --- Tips & sanity checks ---
with st.expander("Tips & sanity checks"):
    st.markdown(
        """
- **1 L/min = 1,000 mL/min = 1,000,000 µL/min = 1,000,000,000 nL/min**  
- **1 L/min = 60 L/h = 60,000 mL/h = 60,000,000 µL/h**  
- Type `uL` if you prefer — it’s accepted as an alias for `µL`.
- Internal base unit is **L/min** to maintain precision across conversions.
- Control rounding and scientific notation from the sidebar.
        """
    )
