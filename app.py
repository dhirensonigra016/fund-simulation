import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
from streamlit_gsheets import GSheetsConnection
from streamlit_oauth import OAuth2Component

# ---------------------------------------------------------
# 1. Configuration and Setup
# ---------------------------------------------------------
st.set_page_config(page_title="Mutual Fund Simulator", layout="centered")

# Set up OAuth component
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]
AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "openid email profile"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, None)

# ---------------------------------------------------------
# 2. Simulation Function
# ---------------------------------------------------------
# (This function remains exactly the same as our previous successful version)
def run_simulation(data, num_simulations=5000):
    results = []
    for isin in data.columns:
        valid_returns = data[isin].dropna().values
        if len(valid_returns) < 6:
            continue
            
        if np.mean(valid_returns) > 1.0 or np.mean(valid_returns) < -1.0:
            valid_returns = valid_returns / 100.0
            
        sim_results = {5: [], 10: [], 15: [], 20: [], 25: [], 30: []}
        
        for _ in range(num_simulations):
            sample = np.random.choice(valid_returns, size=6, replace=False)
            
            cum_5  = (1 + sample[0])**5
            cum_10 = cum_5 * ((1 + sample[1])**5)
            cum_15 = cum_10 * ((1 + sample[2])**5)
            cum_20 = cum_15 * ((1 + sample[3])**5)
            cum_25 = cum_20 * ((1 + sample[4])**5)
            cum_30 = cum_25 * ((1 + sample[5])**5)
            
            sim_results[5].append((cum_5 ** (1/5)) - 1)
            sim_results[10].append((cum_10 ** (1/10)) - 1)
            sim_results[15].append((cum_15 ** (1/15)) - 1)
            sim_results[20].append((cum_20 ** (1/20)) - 1)
            sim_results[25].append((cum_25 ** (1/25)) - 1)
            sim_results[30].append((cum_30 ** (1/30)) - 1)
            
        row = {'ISIN code': isin}
        for years in [30, 25, 20, 15, 10, 5]:
            row[f'{years} year min (%)'] = round(np.min(sim_results[years]) * 100, 2)
            row[f'{years} year average (%)'] = round(np.mean(sim_results[years]) * 100, 2)
            row[f'{years} year max (%)'] = round(np.max(sim_results[years]) * 100, 2)
            
        results.append(row)
    return pd.DataFrame(results)

# ---------------------------------------------------------
# 3. Authentication & Main App Logic
# ---------------------------------------------------------
st.title("📈 Mutual Fund Return Simulator")

# Check if user is logged in
if "user_email" not in st.session_state:
    st.write("### 🔒 Secure Access Only")
    st.write("Please log in with your **@nobias.com** Google account to access the simulator.")
    
    # Show the Google login button
    result = oauth2.authorize_button("Sign in with Google", REDIRECT_URI, SCOPE)
    
    if result and "token" in result:
        # Get the access token and fetch user details from Google
        token = result.get("token").get("access_token")
        user_info = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={token}").json()
        
        email = user_info.get("email", "")
        
        # Verify the domain
        if email.endswith("@nobias.com"):
            st.session_state["user_email"] = email
            st.rerun() # Refresh the page to show the app
        else:
            st.error(f"Access Denied: The email {email} is not authorized. You must use a @nobias.com account.")

# If the user is logged in and verified, show the actual app
else:
    st.success(f"Welcome, {st.session_state['user_email']}!")
    
    if st.button("Log Out"):
        del st.session_state["user_email"]
        st.rerun()
        
    st.write("Fetch historical rolling returns and run 5,000 simulations securely.")

    if st.button("Calculate Now"):
        with st.spinner("Securely fetching private data and running 5000 simulations..."):
            try:
                # Use Streamlit's official Google Sheets connection to read the private sheet using secrets
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(spreadsheet=st.secrets["private_sheet_url"])
                
                # Run the simulation
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
                st.error(f"An error occurred while connecting to the sheet or running the simulation: {e}")
