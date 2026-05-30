import io
import openpyxl
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Droplet Size Calculator", layout="wide")
st.title("Droplet Size Calculator")


def calculate(divisions_and_counts, conv):
    df_dict = {"D": [], "N": [], "DxN": [], "D3": [], "D3xN": []}
    for T, N in divisions_and_counts:
        D3 = T * T * T
        df_dict["D"].append(T)
        df_dict["N"].append(N)
        df_dict["DxN"].append(T * N)
        df_dict["D3"].append(D3)
        df_dict["D3xN"].append(D3 * N)

    df = pd.DataFrame(df_dict)
    df["percentage_of_total"] = (df.DxN / df.DxN.sum()) * 100
    df["accumulative_percentage"] = df["percentage_of_total"].cumsum()
    df["actual_droplet_size(DxCF)"] = df.D * conv
    df["D3_percentage_of_total"] = (df.D3xN / df.D3xN.sum()) * 100
    df["D3_accumulative_percentage"] = df["D3_percentage_of_total"].cumsum()
    df = df.set_index(df.D)
    df["DxN_sum"] = df.DxN.sum()
    df["N_sum"] = df.N.sum()
    df["D3xN_sum"] = df.D3xN.sum()

    poslednji_pre_50 = df[df.accumulative_percentage < 50].iloc[-1]
    prvi_posle_50 = df[df.accumulative_percentage >= 50].iloc[0]
    D3_poslednji_pre_50 = df[df.D3_accumulative_percentage < 50].iloc[-1]
    D3_prvi_posle_50 = df[df.D3_accumulative_percentage >= 50].iloc[0]

    Y, J = poslednji_pre_50.accumulative_percentage, poslednji_pre_50.D
    X, K = prvi_posle_50.accumulative_percentage, prvi_posle_50.D
    Y3, J3 = D3_poslednji_pre_50.D3_accumulative_percentage, D3_poslednji_pre_50.D
    X3, K3 = D3_prvi_posle_50.D3_accumulative_percentage, D3_prvi_posle_50.D

    NM = (K + ((50 - X) / (Y - X)) * (J - K)) * conv
    VM = (K3 + ((50 - X3) / (Y3 - X3)) * (J3 - K3)) * conv

    df["LMD"] = NM
    df["VMD"] = VM
    df["CF"] = conv
    return df, NM, VM


def show_results(df, NM, VM, label):
    st.subheader(label)
    col1, col2 = st.columns(2)
    col1.metric("Number Median Diameter (NMD)", f"{NM:.2f} µm")
    col2.metric("Volume Median Diameter (VMD)", f"{VM:.2f} µm")
    with st.expander("Full data table"):
        st.dataframe(df)
    fname = label.replace(" ", "_")
    col_csv, col_xlsx = st.columns(2)

    csv = df.to_csv().encode("utf-8")
    col_csv.download_button(
        label=f"Download CSV — {label}",
        data=csv,
        file_name=f"{fname}.csv",
        mime="text/csv",
    )

    xlsx_buf = io.BytesIO()
    df.to_excel(xlsx_buf, index=True)
    col_xlsx.download_button(
        label=f"Download Excel — {label}",
        data=xlsx_buf.getvalue(),
        file_name=f"{fname}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def parse_excel(file):
    wb = openpyxl.load_workbook(file)
    ws = wb["Sheet1"]

    # Conversion factor from A1: "faktor konverzije = 3.17"
    conv_raw = ws["A1"].value or ""
    conv = float(conv_raw.split("=")[1].strip()) if "=" in conv_raw else None

    # Detect localities by scanning row 3 for non-empty cells
    localities = []
    row3 = list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]
    for col_idx, cell_val in enumerate(row3):
        if cell_val and isinstance(cell_val, str) and "LOKALITET" in cell_val.upper():
            localities.append({"name": cell_val.strip(), "div_col": col_idx, "n_col": col_idx + 1})

    results = []
    for loc in localities:
        rows = []
        for row in ws.iter_rows(min_row=5, values_only=True):
            T = row[loc["div_col"]]
            N = row[loc["n_col"]]
            if T is None:
                break
            rows.append((int(T), int(N)))
        results.append({"name": loc["name"], "data": rows})

    return conv, results


tab_upload, tab_manual = st.tabs(["Upload Excel", "Manual Entry"])

# ── Upload tab ────────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("Upload your Excel file. The conversion factor and both localities will be detected automatically.")
    uploaded = st.file_uploader("Choose an .xlsx file", type=["xlsx"])

    if uploaded:
        try:
            conv, localities = parse_excel(uploaded)
        except Exception as e:
            st.error(f"Could not parse file: {e}")
            localities = []
            conv = None

        if conv is not None:
            st.info(f"Conversion factor detected: **{conv}**")
        else:
            conv = st.number_input("Conversion factor not found — enter it manually", min_value=0.01, value=3.17, step=0.01, key="upload_conv")

        if localities:
            for loc in localities:
                try:
                    df, NM, VM = calculate(loc["data"], conv)
                    show_results(df, NM, VM, loc["name"])
                except Exception as e:
                    st.error(f"Error calculating {loc['name']}: {e}")
        else:
            st.warning("No localities found in the file. Make sure locality names contain 'LOKALITET'.")

# ── Manual entry tab ──────────────────────────────────────────────────────────
with tab_manual:
    st.markdown("Enter data manually for one locality at a time.")

    col_a, col_b, col_c = st.columns(3)
    locality_name = col_a.text_input("Locality name", value="Locality 1")
    num_divisions = col_b.number_input("Number of divisions", min_value=1, max_value=100, value=25, step=1)
    conv_manual = col_c.number_input("Conversion factor", min_value=0.01, value=3.17, step=0.01)

    st.markdown("**Enter droplet count per division:**")
    cols = st.columns(5)
    counts = []
    for i in range(int(num_divisions)):
        T = i + 1
        n = cols[i % 5].number_input(f"Division {T}", min_value=0, value=0, step=1, key=f"div_{T}")
        counts.append((T, n))

    if st.button("Calculate", type="primary"):
        try:
            df, NM, VM = calculate(counts, conv_manual)
            show_results(df, NM, VM, locality_name)
        except Exception as e:
            st.error(f"Calculation error: {e}")
