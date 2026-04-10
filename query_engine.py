from analytics_engine import top_product, sales_by_branch, total_sales

def handle_query(query, df):
    query = query.lower()

    if "top product" in query or "highest sales" in query:
        return top_product(df)

    elif "branch" in query:
        return sales_by_branch(df)

    elif "total" in query:
        return total_sales(df)

    else:
        return "Query not understood"