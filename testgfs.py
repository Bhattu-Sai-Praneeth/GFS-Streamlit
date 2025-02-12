import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt
from pathlib import Path
import pandas_ta as ta
import os

# Set up page configuration and custom CSS
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .sidebar .sidebar-content {
        background: #ffffff;
    }
    h1 {
        color: #2a3f5f;
    }
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- VIX Functions ---
def fetch_vix():
    """Fetches the latest VIX closing value using yfinance."""
    vix = yf.Ticker("^VIX")
    vix_data = vix.history(period="1d")
    if not vix_data.empty:
        return vix_data['Close'].iloc[0]
    return None

# --- GFS Analysis Functions ---
def append_row(df, row):
    """Appends a new row to a pandas DataFrame if the row is not empty."""
    if row.isnull().all():
        return df
    return pd.concat([df, pd.DataFrame([row], columns=row.index)]).reset_index(drop=True)

def getRSI14_and_BB(csvfilename):
    """Calculates RSI (14 period) and Bollinger Bands (20 period, 2 std.dev) for a given CSV file."""
    if Path(csvfilename).is_file():
        try:
            df = pd.read_csv(csvfilename)
            if df.empty or 'Close' not in df.columns:
                return 0.00, 0.00, 0.00, 0.00
            else:
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                df['rsi14'] = ta.rsi(df['Close'], length=14)
                bb = ta.bbands(df['Close'], length=20)
                if bb is None or df['rsi14'] is None:
                    return 0.00, 0.00, 0.00, 0.00
                df['lowerband'] = bb['BBL_20_2.0']
                df['middleband'] = bb['BBM_20_2.0']
                if pd.isna(df['rsi14'].iloc[-1]) or pd.isna(df['lowerband'].iloc[-1]) or pd.isna(df['middleband'].iloc[-1]):
                    return 0.00, 0.00, 0.00, 0.00
                else:
                    rsival = df['rsi14'].iloc[-1].round(2)
                    ltp = df['Close'].iloc[-1].round(2)
                    lowerband = df['lowerband'].iloc[-1].round(2)
                    middleband = df['middleband'].iloc[-1].round(2)
                    return rsival, ltp, lowerband, middleband
        except Exception as e:
            return 0.00, 0.00, 0.00, 0.00
    else:
        return 0.00, 0.00, 0.00, 0.00

def dayweekmonth_datasets(symbol, symbolname, index_code):
    """Calculates RSI, Bollinger Bands, and other metrics for daily, weekly, and monthly data."""
    symbol_with_underscore = symbol.replace('.', '_')
    
    daylocationstr = f'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Daily_data/{symbol_with_underscore}.csv'
    weeklocationstr = f'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Weekly_data/{symbol_with_underscore}.csv'
    monthlocationstr = f'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Monthly_data/{symbol_with_underscore}.csv'

    cday = dt.datetime.today().strftime('%d/%m/%Y')
    dayrsi14, dltp, daylowerband, daymiddleband = getRSI14_and_BB(daylocationstr)
    weekrsi14, wltp, weeklowerband, weekmiddleband = getRSI14_and_BB(weeklocationstr)
    monthrsi14, mltp, monthlowerband, monthmiddleband = getRSI14_and_BB(monthlocationstr)

    new_row = pd.Series({
        'entrydate': cday,
        'indexcode': index_code,
        'indexname': symbolname,
        'dayrsi14': dayrsi14,
        'weekrsi14': weekrsi14,
        'monthrsi14': monthrsi14,
        'dltp': dltp,
        'daylowerband': daylowerband,
        'daymiddleband': daymiddleband,
        'weeklowerband': weeklowerband,
        'weekmiddleband': weekmiddleband,
        'monthlowerband': monthlowerband,
        'monthmiddleband': monthmiddleband
    })
    return new_row

def generateGFS(scripttype):
    """Generates the GFS report based on the provided scripttype."""
    indicesdf = pd.DataFrame(columns=['entrydate', 'indexcode', 'indexname', 'dayrsi14', 
                                       'weekrsi14', 'monthrsi14', 'dltp', 'daylowerband', 
                                       'daymiddleband', 'weeklowerband', 'weekmiddleband', 
                                       'monthlowerband', 'monthmiddleband'])

    fname = f'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/{scripttype}.csv'
    try:
        with open(fname) as f:
            for line in f:
                if "," not in line:
                    continue
                symbol, symbolname = line.split(",")[0], line.split(",")[1]
                symbol = symbol.strip()
                new_row = dayweekmonth_datasets(symbol, symbolname, symbol)
                indicesdf = append_row(indicesdf, new_row)
    except Exception as e:
        st.error("Error generating GFS report.")
    return indicesdf

def read_indicesstocks(file_path):
    """Reads the indicesstocks.csv file and returns a dictionary."""
    indices_dict = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) > 1:
                    index_code = parts[0].strip()
                    stocks = [stock.strip() for stock in parts[1:]]
                    indices_dict[index_code] = stocks
    except Exception as e:
        pass
    return indices_dict

# --- Streamlit UI ---
st.title("📈 Stock Analysis Dashboard")
st.markdown("### Financial System Analysis Tool")

# Sidebar information
st.sidebar.header("About")
st.sidebar.markdown("""
This tool analyzes financial instruments using:
- **Volatility Index indicates market volatility and investor fear**
- **RSI (14-period)**
- **Bollinger Bands (20-period)**
- Multi-timeframe analysis (Daily/Weekly/Monthly)
""")
st.sidebar.download_button(
    label="Download Sample Data",
    data=open(r'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/indicesdf.csv', 'rb'),
    file_name="sample_data.csv",
    mime="text/csv"
)

# Main button: Run Full Analysis with integrated VIX check
if st.button("Run Full Analysis"):
    # --- Step 1: Check the VIX value ---
    with st.spinner("Fetching VIX data..."):
        vix_value = fetch_vix()
    if vix_value is None:
        st.error("Could not fetch VIX data. Please try again later.")
    elif vix_value > 20:
        st.warning(f"VIX is above the acceptable range (VIX: {vix_value}). GFS analysis will not proceed as the market is not in a tradable condition. The GFS strategy is not recommended. ")
    else:
        st.success(f"VIX is within the acceptable range (VIX: {vix_value}). Proceeding with GFS Analysis.")
        # --- Step 2: Run the GFS Analysis ---
        with st.spinner('Processing indices...'):
            # Create necessary directories if they do not exist
            os.makedirs('E:/new .data/Major pro source codes/Major pro source codes/DATASETS', exist_ok=True)
            os.makedirs('E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Daily_data', exist_ok=True)
            os.makedirs('E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Weekly_data', exist_ok=True)
            os.makedirs('E:/new .data/Major pro source codes/Major pro source codes/DATASETS/Monthly_data', exist_ok=True)

            # Generate GFS report for indices
            df3 = generateGFS('indicesdf')

            # Filter the report based on RSI criteria
            df4 = df3.loc[
                df3['monthrsi14'].between(40, 60) &
                df3['weekrsi14'].between(40, 60) &
                df3['dayrsi14'].between(40, 60)
            ]
            
            filtered_indices_path = r'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/filtered_indices_output.csv'
            filtered_indexcodes = df4[['indexcode']]
            filtered_indexcodes.to_csv(filtered_indices_path, index=False)

            # Display qualified indices
            st.markdown("### Qualified Indices")
            if filtered_indexcodes.empty:
                st.warning("NO INDICES QUALIFY THE GFS CRITERIA")
            else:
                st.dataframe(df4.style.format({
                    'dayrsi14': '{:.2f}',
                    'weekrsi14': '{:.2f}',
                    'monthrsi14': '{:.2f}',
                    'dltp': '{:.2f}'
                }), use_container_width=True)

                # Process and display stocks for matched indices
                st.markdown("### Qualified Stocks")
                indicesstocks_path = r'E:/new .data/Major pro source codes/Major pro source codes/DATASETS/indicesstocks.csv'
                indicesstocks = read_indicesstocks(indicesstocks_path)
                filtered_indices = filtered_indexcodes['indexcode'].tolist()

                results_df = pd.DataFrame(columns=['entrydate', 'indexcode', 'indexname', 'dayrsi14', 
                                                   'weekrsi14', 'monthrsi14', 'dltp', 'daylowerband', 
                                                   'daymiddleband', 'weeklowerband', 'weekmiddleband', 
                                                   'monthlowerband', 'monthmiddleband'])
                for index in filtered_indices:
                    if index in indicesstocks:
                        stocks = indicesstocks[index]
                        for stock in stocks[1:]:
                            if stock:
                                matched_row = dayweekmonth_datasets(stock, stock, index)
                                results_df = append_row(results_df, matched_row)

                if not results_df.empty:
                    results_df1 = results_df.loc[
                        results_df['monthrsi14'].between(40, 60) &
                        results_df['weekrsi14'].between(40, 60) &
                        results_df['dayrsi14'].between(40, 60)
                    ]
                    results_df1.to_csv(filtered_indices_path, index=False)
                    st.dataframe(results_df1.style.format({
                        'dayrsi14': '{:.2f}',
                        'weekrsi14': '{:.2f}',
                        'monthrsi14': '{:.2f}',
                        'dltp': '{:.2f}'
                    }), use_container_width=True)
                else:
                    st.warning("NO STOCKS QUALIFY THE GFS CRITERIA")
