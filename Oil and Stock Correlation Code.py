import subprocess
import sys

# Install required libraries
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "seaborn"])



import yfinance as yf
import pandas as pd



#import oil price data
oil_data = yf.download('CL=F', start='2000-01-03', end='2024-01-01')
print(oil_data.head())

#import all sector data from 2000-01-03 to today and title each dataframe with the sector name
sectors = {
    'Technology': 'XLK',
    'Financials': 'XLF',
    'Healthcare': 'XLV',
    'Consumer Discretionary': 'XLY',
    'Energy': 'XLE',
    'Industrials': 'XLI',
    'Materials': 'XLB',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE'
}

sector_data = {}
for sector, ticker in sectors.items():
    data = yf.download(ticker, start='2000-01-03', end='2024-01-01')
    sector_data[sector] = data

#print the first few rows of each sector data to ensure correct formatting
for sector, data in sector_data.items():
    print(f"{sector} data:")
    print(data.head())

print(oil_data.head())

#remove high, low, open from the oil data and sector data to focus on adjusted close price and trade volume
oil_data = oil_data[['Close', 'Volume']]
for sector in sector_data:
    sector_data[sector] = sector_data[sector][['Close', 'Volume']]


#remove any rows with missing values from the oil data and sector data
oil_data.dropna(inplace=True)
for sector in sector_data:
    sector_data[sector].dropna(inplace=True)

# create % change variables for the oil data and sector data close column to calculate returns

oil_data['CReturns'] = oil_data['Close'].pct_change()
for sector in sector_data:
    sector_data[sector]['CReturns'] = sector_data[sector]['Close'].pct_change()  

#create % change variables for the volume column for the oil data and sector data (can replace Vreturns with CReturns keeping the rest of the code the same to see the volume of trades correlation)

oil_data['Vreturns'] = oil_data['Volume'].pct_change()
for sector in sector_data:
    sector_data[sector]['Vreturns'] = sector_data[sector]['Volume'].pct_change()  



#print the first few rows of the oil data and sector data to ensure the returns column was added correctly
print("Oil data with returns:")
print(oil_data.head())
for sector, data in sector_data.items():
    print(f"{sector} data with returns:")
    print(data.head())



#create a dataframe to hold only the creturns for the oil data and sector data excluding real estate since it starts in 2015
returns_data = pd.DataFrame()
returns_data['Oil'] = oil_data['CReturns']
for sector in sector_data:
    if sector != 'Real Estate':
        returns_data[sector] = sector_data[sector]['CReturns']
print("Returns dataframe:")
print(returns_data.head())

#create a dataframe to hold only the creturns for the oil data and real estate data
real_estate_returns = pd.DataFrame()
real_estate_returns['Oil'] = oil_data['CReturns']
real_estate_returns['Real Estate'] = sector_data['Real Estate']['CReturns']
print("Real Estate Returns dataframe:")
print(real_estate_returns.head())


#run a correlation analysis between the oil returns and the sector returns 
correlation_matrix = returns_data.corr()
print("Correlation Matrix:")
print(correlation_matrix)

#remove the correlation between the sectors and themselves to focus on the correlation between the oil returns and the sector returns
correlation_matrix = correlation_matrix.drop(index=returns_data.columns, columns=returns_data.columns)
#print the correlation matrix to ensure the correlation between the oil returns and the sector returns is correct
print("Correlation Matrix without self-correlation:")
print(correlation_matrix)


#run a correlation analysis between the oil returns and the real estate returns
real_estate_correlation = real_estate_returns.corr()
print("Real Estate Correlation Matrix:")
print(real_estate_correlation)

#add the real estate column from the real estate correlation matrix DF to the correlation matrix DF and remove the oil column and all sector rows so the correlation matrix shows as one clean row
correlation_matrix = returns_data.corr()
correlation_matrix = correlation_matrix.loc[['Oil']].drop(columns=['Oil'])
correlation_matrix['Real Estate'] = real_estate_correlation.loc['Oil', 'Real Estate']
print("Correlation Matrix with Real Estate:")
print(correlation_matrix)


#create a lead and lag for creturns for each sector at 7 days 14 days 30 days and 60 days
lead_lag_intervals = [7, 14, 30, 60]
for interval in lead_lag_intervals:
    for sector in sector_data:
        sector_data[sector][f'CReturns_lag_{interval}'] = sector_data[sector]['CReturns'].shift(interval)
        sector_data[sector][f'CReturns_lead_{interval}'] = sector_data[sector]['CReturns'].shift(-interval)

#remove rows with NaN values created by lead/lag shifts
oil_data.dropna(inplace=True)
for sector in sector_data:
    sector_data[sector].dropna(inplace=True)

#create a data frame for each sector their lead, and include the oil prices
sector_lead_data = {}
for sector, data in sector_data.items():
    df = pd.DataFrame()
    df['Oil'] = oil_data['CReturns']
    for interval in lead_lag_intervals:
        df[f'{sector}_Lead_{interval}'] = data[f'CReturns_lead_{interval}']
    sector_lead_data[sector] = df.dropna()
    print(f"{sector} lead dataframe:")
    print(sector_lead_data[sector].head())

#create a df for each sector and their lag (as the lag will be starting from a different date)
sector_lag_data = {}
for sector, data in sector_data.items():
    df = pd.DataFrame()
    df['Oil'] = oil_data['CReturns']
    for interval in lead_lag_intervals:
        df[f'{sector}_Lag_{interval}'] = data[f'CReturns_lag_{interval}']
    sector_lag_data[sector] = df.dropna()
    print(f"{sector} lag dataframe:")
    print(sector_lag_data[sector].head())

# create a correlation matrix for each sector's lead data and one for each sector's lag data
lead_corr_matrices = {}
lag_corr_matrices = {}
for sector, df in sector_lead_data.items():
    corr = df.corr()
    corr = corr.loc[['Oil']].drop(columns=['Oil'])
    lead_corr_matrices[sector] = corr
    print(f"{sector} lead correlation matrix:")
    print(corr)

for sector, df in sector_lag_data.items():
    corr = df.corr()
    corr = corr.loc[['Oil']].drop(columns=['Oil'])
    lag_corr_matrices[sector] = corr
    print(f"{sector} lag correlation matrix:")
    print(corr)


#combine the correlation matrixs with the main one
combined_matrix = pd.DataFrame(
    index=[
        'Lag 60',
        'Lag 30',
        'Lag 14',
        'Lag 7',
        'Main',
        'Lead 7',
        'Lead 14',
        'Lead 30',
        'Lead 60'
    ],
    columns=correlation_matrix.columns
)

# fill main correlation row
for sector in correlation_matrix.columns:
    combined_matrix.loc['Main', sector] = correlation_matrix.loc['Oil', sector]

# fill lag rows in descending order
for sector, corr_df in lag_corr_matrices.items():
    for interval in sorted(lead_lag_intervals, reverse=True):
        col_name = f'{sector}_Lag_{interval}'
        row_name = f'Lag {interval}'
        if col_name in corr_df.columns:
            combined_matrix.loc[row_name, sector] = corr_df.loc['Oil', col_name]

# fill lead rows in ascending order
for sector, corr_df in lead_corr_matrices.items():
    for interval in lead_lag_intervals:
        col_name = f'{sector}_Lead_{interval}'
        row_name = f'Lead {interval}'
        if col_name in corr_df.columns:
            combined_matrix.loc[row_name, sector] = corr_df.loc['Oil', col_name]

print("Combined correlation matrix with lag/main/lead rows:")
print(combined_matrix)

#create a heatmap of the correlation matrix using seaborn
import matplotlib.pyplot as plt

import seaborn as sns

plt.figure(figsize=(12, 8))
sns.heatmap(combined_matrix.astype(float), annot=True, cmap='coolwarm', center=0, linewidths=0.5, linecolor='white')
plt.title('Correlation Heatmap of Oil Returns and Sector Lead/Lag Relationships')
plt.xlabel('Sectors')
plt.ylabel('Lead/Lag / Main')
plt.tight_layout()
plt.show()
