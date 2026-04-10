

def top_product(df):
    # returns product with highest total sales
    return df.groupby("product")["sales"].sum().idxmax()


def sales_by_branch(df):
    # returns dict of branch -> total sales
    return df.groupby("branch")["sales"].sum().to_dict()


def total_sales(df):
    # returns total sales number
    return float(df["sales"].sum())