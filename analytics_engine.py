

def top_product(df):
    # returns product with highest total sales
    return df.groupby("product")["sales"].sum().idxmax()


def sales_by_branch(df):
    # returns dict of branch -> total sales
    return df.groupby("branch")["sales"].sum().to_dict()


def total_sales(df):
    # returns total sales number
    return float(df["sales"].sum())


# --- Smart document analysis functions ---
def extract_document_metrics(df):
    """
    Extract key fields like total, tax, amount from structured OCR DataFrame
    """
    metrics = {}

    if "field" in df.columns and "value" in df.columns:
        for _, row in df.iterrows():
            field = str(row["field"]).lower()
            value = row["value"]

            if any(k in field for k in ["total", "amount"]):
                metrics["total"] = value
            elif "tax" in field or "gst" in field:
                metrics["tax"] = value
            elif "date" in field:
                metrics["date"] = value

    return metrics


def document_insights(df):
    """
    Generate insights for invoice/receipt-like documents
    """
    insights = []
    metrics = extract_document_metrics(df)

    if not metrics:
        return ["No structured financial data detected"]

    if "total" in metrics:
        insights.append(f"Total amount detected: {metrics['total']}")

    if "tax" in metrics and "total" in metrics:
        try:
            tax_ratio = float(metrics["tax"]) / float(metrics["total"])
            insights.append(f"Tax is approximately {tax_ratio*100:.2f}% of total")
        except:
            pass

    if "date" in metrics:
        insights.append(f"Transaction date: {metrics['date']}")

    return insights


def analyze_document(df):
    """
    Main entry point for document-specific analysis
    """
    insights = document_insights(df)

    return {
        "type": "document_analysis",
        "insights": insights
    }