import streamlit as st
import pandas as pd
import numpy as np
import io

# ---------------------------------------------------------
# 1. Configuration and Setup
# ---------------------------------------------------------
st.set_page_config(page_title="Mutual Fund Simulator", layout="centered")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1T5hg2yVqDrkAfVmLTeuuEDYhDrvyGQQi6IKR3EL1EEM/export?format=csv"

# ---------------------------------------------------------
# 2. Simulation Function
# ---------------------------------------------------------
def run_simulation(data, num_simulations=5000):
    """
    Runs Monte Carlo simulations on the provided dataframe.
    Calculates cumulative returns, then annualized returns,
    and returns the min, average, and max as percentages.
    """
    results = []
    
    for isin in data.columns:
        # Drop any empty/NaN values
        valid_returns = data[isin].dropna().values
        
        if len(valid_returns) < 6:
            st.warning(f"Not enough data for {isin}. Skipping.")
            continue
            
        # SAFETY CHECK: If returns look like percentages, convert to decimals for the math
        if np.mean(valid_returns) > 1.0 or np.mean(valid_returns) < -1.0:
            valid_returns = valid_returns / 100.0
            
        sim_results = {5: [], 10: [], 15: [], 20: [], 25: [], 30: []}
        
        for _ in range(num_simulations):
            # Select 6 random return values without replacement
            sample = np.random.choice(valid_returns, size=6, replace=False)
            
            # Step 1: Calculate CUMULATIVE returns using the power function
            cum_5  = (1 + sample[0])**5
            cum_10 = cum_5 * ((1 + sample[1])**5)
            cum_15 = cum_10 * ((1 + sample[2])**5)
            cum_20 = cum_15 * ((1 + sample[3])**5)
            cum_25 = cum_20 * ((1 + sample[4])**5)
            cum_30 = cum_25 * ((1 + sample[5])**5)
            
            # Step 2: Calculate ANNUALIZED returns from the cumulative values
            ann_5  = (cum_5 ** (1/5)) - 1
            ann_10 = (cum_10 ** (1/10)) - 1
            ann_15 = (cum_15 ** (1/15)) - 1
            ann_20 = (cum_20 ** (1/20)) - 1
            ann_25 = (cum_25 ** (1/25)) - 1
            ann_30 = (cum_30 ** (1/30)) - 1
            
            # Store the annualized results
            sim_results[5].append(ann_5)
            sim_results[10].append(ann_10)
            sim_results[15].append(ann_15)
            sim_results[20].append(ann_20)
            sim_results[25].append(ann_25)
            sim_results[30].append(ann_30)
            
        # Step 3: Find min, mean, and max, and convert them to percentages
        row = {'ISIN code': isin}
        for years in [30, 25, 20, 15, 10, 5]:
            row[f'{years} year min (%)'] = round(np.min(sim_results[years]) * 100, 2)
            row[f'{years} year average (%)'] = round(np.mean(sim_results[years]) * 100, 2)
            row[f'{years} year max (%)'] = round(np.max(sim_results[years]) * 100, 2)
            
        results.append(row)
        
    return pd.DataFrame(results)

# ---------------------------------------------------------
# 3. Streamlit User Interface
# ---------------------------------------------------------
st.title("📈 Mutual Fund Return Simulator")
st.write("""
This application fetches historical rolling returns and runs 5,000 simulations 
to project 5, 10, 15, 20, 25, and 30-year **annualized** performance (as percentages) for each fund.
""")

if st.button("Calculate Now"):
    with st.spinner("Fetching data and running 5000 simulations..."):
        try:
            df = pd.read_csv(SHEET_URL)
            final_df = run_simulation(df, num_simulations=5000)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Simulations')
            
            excel_data = output.getvalue()
            
            st.success("Simulation complete! You can now download your results.")
            
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name="annualized_simulation_results_pct.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.write("### Preview of Results")
            st.dataframe(final_df.head())
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
