

import pandas as pd
import os

def clean_data(df, file_name):
    df_clean = df.copy()

    # Remove duplicates
    df_clean = df_clean.drop_duplicates()

    # Handle missing values
    for col in df_clean.columns:
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].fillna(0)
        else:
            df_clean[col] = df_clean[col].fillna("unknown")

    # Convert ONLY likely datetime columns (avoid numeric corruption)
    for col in df_clean.columns:
        if df_clean[col].dtype == "object":
            try:
                converted = pd.to_datetime(df_clean[col], errors="coerce")
                if converted.notna().sum() > 0:
                    df_clean[col] = converted
            except:
                pass

    # Save cleaned file
    os.makedirs("processed", exist_ok=True)
    clean_path = f"processed/cleaned_{file_name}"
    df_clean.to_csv(clean_path, index=False)

    return df_clean, clean_path