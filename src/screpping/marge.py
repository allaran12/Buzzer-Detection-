"""Gabungkan semua data/raw/*.csv -> data/all_tweets.csv
Jalankan: python merge.py
"""
import glob

import pandas as pd

files = glob.glob("data/raw/*.csv")
assert files, "Belum ada file di data/raw/. Scrape dulu lewat app.py"

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df = df.drop_duplicates(subset=["id", "isu"])  # JANGAN dedup berdasarkan text!
df.to_csv("data/all_tweets.csv", index=False)

print(df.groupby("isu").agg(
    tweet=("id", "count"),
    akun=("username", "nunique"),
    reply=("is_reply", "sum"),
    retweet=("is_rt", "sum"),
))
print("\nTotal:", len(df), "tweet,", df["username"].nunique(), "akun unik")