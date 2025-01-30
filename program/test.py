import pandas as pd

df = pd.read_csv("car_prices.csv")

df['saledate'] = pd.to_datetime(df['saledate'], format='%a %b %d %Y %H:%M:%S GMT%z (%w)')