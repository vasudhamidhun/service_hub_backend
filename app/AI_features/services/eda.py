
# from .data_loader import load_dataset
# import pandas as pd


# def get_dataset_overview():
#     df = load_dataset()

#     return {
#         "total_rows": int(df.shape[0]),
#         "total_columns": int(df.shape[1]),
#         "column_names": df.columns.tolist(),
#         "duplicate_rows": int(df.duplicated().sum()),
#     }


# def get_column_information():
#     df = load_dataset()

#     return {
#         column: {
#             "data_type": str(df[column].dtype),
#             "non_null_count": int(df[column].count()),
#             "null_count": int(df[column].isnull().sum()),
#             "unique_values": int(df[column].nunique()),
#         }
#         for column in df.columns
#     }


# def get_missing_value_analysis():
#     df = load_dataset()

#     missing = df.isnull().sum()

#     return {
#         column: int(count)
#         for column, count in missing.items()
#     }


# def get_rating_analysis():
#     df = load_dataset()

#     ratings = pd.to_numeric(
#         df["rating"],
#         errors="coerce"
#     )

#     return {
#         "valid_ratings": int(ratings.count()),
#         "invalid_ratings": int(ratings.isnull().sum()),
#         "average_rating": round(float(ratings.mean()), 2),
#         "minimum_rating": float(ratings.min()),
#         "maximum_rating": float(ratings.max()),
#         "rating_distribution": {
#             str(rating): int(count)
#             for rating, count in ratings.value_counts().sort_index().items()
#         }
#     }


# def get_review_text_analysis():
#     df = load_dataset()

#     title = df["review_title"].fillna("").astype(str)
#     content = df["review_content"].fillna("").astype(str)

#     return {
#         "total_review_records": len(df),
#         "empty_titles": int((title.str.strip() == "").sum()),
#         "empty_contents": int((content.str.strip() == "").sum()),
#         "average_title_length": round(float(title.str.len().mean()), 2),
#         "average_content_length": round(float(content.str.len().mean()), 2),
#         "reviews_containing_urls": int(
#             content.str.contains(r"https?://", regex=True).sum()
#         )
#     }


# def get_review_structure_analysis():
#     df = load_dataset()

#     review_id_counts = (
#         df["review_id"]
#         .fillna("")
#         .astype(str)
#         .str.split(",")
#         .str.len()
#     )

#     review_title_counts = (
#         df["review_title"]
#         .fillna("")
#         .astype(str)
#         .str.split(",")
#         .str.len()
#     )

#     review_content_counts = (
#         df["review_content"]
#         .fillna("")
#         .astype(str)
#         .str.split(",")
#         .str.len()
#     )

#     return {
#         "average_review_ids_per_product": round(
#             float(review_id_counts.mean()), 2
#         ),
#         "average_review_titles_per_product": round(
#             float(review_title_counts.mean()), 2
#         ),
#         "average_content_comma_segments": round(
#             float(review_content_counts.mean()), 2
#         ),
#         "id_title_mismatch_records": int(
#             (review_id_counts != review_title_counts).sum()
#         ),
#         "total_records": len(df)
#     }


# def inspect_review_records(limit=5):
#     df = load_dataset()

#     columns = [
#         "product_id",
#         "review_id",
#         "review_title",
#         "review_content"
#     ]

#     records = df[columns].head(limit)

#     result = []

#     for _, row in records.iterrows():
#         result.append({
#             "product_id": row["product_id"],
#             "review_id": row["review_id"],
#             "review_title": row["review_title"],
#             "review_content": row["review_content"]
#         })

#     return result


