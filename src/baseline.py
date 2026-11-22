import pandas as pd


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Assign quintile scores; higher Recency score means a more recent purchase."""
    result = rfm.copy()
    for column in ("Recency", "Frequency", "Monetary"):
        ascending = column != "Recency"
        ranks = result[column].rank(method="first", ascending=ascending)
        result[f"{column[0]}_score"] = pd.qcut(
            ranks, q=5, labels=[1, 2, 3, 4, 5]
        ).astype(int)

    r_score = result["R_score"]
    f_score = result["F_score"]
    m_score = result["M_score"]
    result["baseline_segment"] = "Regular"
    result.loc[(r_score <= 2) & (f_score <= 2), "baseline_segment"] = "Lost"
    result.loc[(r_score <= 2) & (f_score >= 3), "baseline_segment"] = "At-risk"
    result.loc[(r_score >= 4) & (f_score >= 4) & (m_score >= 4), "baseline_segment"] = "Champions"
    result.loc[(r_score >= 4) & (f_score >= 4) & (m_score < 4), "baseline_segment"] = "Loyal"
    result.loc[(r_score >= 4) & (f_score <= 2), "baseline_segment"] = "New/Promising"
    return result
