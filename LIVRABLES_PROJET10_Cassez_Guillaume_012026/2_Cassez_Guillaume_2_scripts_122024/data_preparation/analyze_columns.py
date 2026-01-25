import pandas as pd
import glob

files = sorted(glob.glob("/home/ser/Bureau/P10_reco_new/news-portal-user-interactions-by-globocom/clicks/clicks_hour_*.csv"))
if not files:
    files = sorted(glob.glob("clicks/clicks_hour_*.csv"))

df = pd.read_csv(files[0])

print("=== click_os ===")
print(df['click_os'].value_counts().head(15))
print(f"\nTotal unique: {df['click_os'].nunique()}")

print("\n=== click_country ===")
print(df['click_country'].value_counts().head(15))
print(f"\nTotal unique: {df['click_country'].nunique()}")

print("\n=== click_region ===")
print(df['click_region'].value_counts().head(15))
print(f"\nTotal unique: {df['click_region'].nunique()}")
