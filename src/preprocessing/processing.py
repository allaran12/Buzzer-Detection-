"""Cleaning + normalisasi + split per isu + standardisasi.
Jalankan: python preprocess.py
Install : pip install emoji scikit-learn pandas joblib
Ubah TRAIN_ISU / VAL_ISU / TEST_ISU sesuai nama isu kamu.
"""
import os
import re

import emoji
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

TRAIN_ISU = ["isu1", "isu2"]
VAL_ISU = ["isu3"]
TEST_ISU = ["isu4"]
NUM_COLS = ["followers", "following", "statuses"]


def clean_bert(t):
    """Format untuk IndoBERTweet: jangan hapus stopword / stemming."""
    t = str(t)
    t = re.sub(r"https?://\S+", "HTTPURL", t)
    t = re.sub(r"@\w+", "@USER", t)
    t = emoji.demojize(t, language="id")
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)  # bangeeet -> bangeet
    return re.sub(r"\s+", " ", t).strip().lower()

df = pd.read_csv("data/all_tweets.csv")
df = df.dropna(subset=["text", "username", "date"])
df = df.drop_duplicates(subset=["id", "isu"])
df["date"] = pd.to_datetime(df["date"], utc=True)
df["created"] = pd.to_datetime(df["created"], utc=True)

df["text_bert"] = df["text"].map(clean_bert)
df = df[df["text_bert"].str.split().str.len() >= 3]

train = df[df["isu"].isin(TRAIN_ISU)].copy()
val = df[df["isu"].isin(VAL_ISU)].copy()
test = df[df["isu"].isin(TEST_ISU)].copy()

for d in (train, val, test):
    d[NUM_COLS] = np.log1p(d[NUM_COLS].clip(lower=0))
scaler = StandardScaler().fit(train[NUM_COLS])
for d in (train, val, test):
    d[NUM_COLS] = scaler.transform(d[NUM_COLS])

os.makedirs("data/processed", exist_ok=True)
for name, d in [("train", train), ("val", val), ("test", test)]:
    d.to_csv(f"data/processed/{name}.csv", index=False)
joblib.dump(scaler, "data/processed/scaler.pkl")

print({"train": len(train), "val": len(val), "test": len(test)})