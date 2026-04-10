import pandas as pd

def profile_data(df):
    profile = {}

    profile["columns"] = list(df.columns)
    profile["num_rows"] = len(df)

    dtypes = {}
    missing = {}

    for col in df.columns:
        missing[col] = int(df[col].isnull().sum())

        # First check numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            dtypes[col] = "numeric"
            continue

        # Then try datetime ONLY for non-numeric
        try:
            converted = pd.to_datetime(df[col], errors="raise")
            # Check if conversion actually makes sense (not all NaT)
            if converted.notna().sum() > 0:
                dtypes[col] = "datetime"
            else:
                dtypes[col] = "text"
        except:
            dtypes[col] = "text"

    profile["dtypes"] = dtypes
    profile["missing_values"] = missing

    return profile