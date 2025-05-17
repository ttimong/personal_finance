import pandas as pd
from werkzeug.datastructures import FileStorage


def load_data(files: list[FileStorage], col_map: dict[str, str]) -> pd.DataFrame:
    """
    Load data from a list of files and map the columns to the specified names.

    Args:
        files (list[FileStorage]): List of file objects to load data from.
        col_map (dict[str, str]): Dictionary mapping original column names to new names.

    Returns:
        pd.DataFrame: DataFrame containing the loaded and mapped data.
    """
    res_df = pd.DataFrame()
    for file in files:
        if file.filename.endswith(".csv"):
            data = pd.read_csv(file)
            data["id"] = range(len(res_df), len(res_df) + len(data))
            res_df = pd.concat([res_df, data[col_map.values()]], ignore_index=True)
        else:
            raise ValueError(
                f"Invalid file type: {file.filename}. Only CSV files are supported."
            )

    res_df.rename(columns={v: k for k, v in col_map.items()}, inplace=True)
    return res_df


def match_data(
    stmt_data: pd.DataFrame,
    manual_data: pd.DataFrame,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Match data from two DataFrames based on date and amount columns.

    Args:
        stmt_data (pd.DataFrame): DataFrame containing statement data.
        manual_data (pd.DataFrame): DataFrame containing manual tracking data.

    Returns:
        tuple[list[dict], list[dict], list[dict]]: Tuple containing three lists:
            - matched data
            - unmatched statement data
            - unmatched manual tracking data
    """
    combine_df = stmt_data.merge(
        manual_data,
        how="outer",
        left_on=["stmt_date", "stmt_amt"],
        right_on=["manual_date", "manual_amt"],
    )
    match_df = combine_df.dropna()
    match_res = [
        {
            "src_stmt": {
                "id": row["stmt_id"],
                "date": row["stmt_date"],
                "amount": row["stmt_amt"],
                "desc": row["stmt_desc"],
            },
            "src_manual": {
                "id": row["manual_id"],
                "date": row["manual_date"],
                "amount": row["manual_amt"],
                "desc": row["manual_desc"],
            },
        }
        for _, row in match_df.iterrows()
    ]

    cc_unmatch_df = combine_df[combine_df["manual_date"].isnull()].copy()
    cc_unmatch_res = [
        {
            "id": row["stmt_id"],
            "date": row["stmt_date"],
            "amount": row["stmt_amt"],
            "desc": row["stmt_desc"],
        }
        for _, row in cc_unmatch_df.iterrows()
    ]
    manual_unmatch_df = combine_df[combine_df["stmt_date"].isnull()].copy()
    manual_unmatch_res = [
        {
            "id": row["manual_id"],
            "date": row["manual_date"],
            "amount": row["manual_amt"],
            "desc": row["manual_desc"],
        }
        for _, row in manual_unmatch_df.iterrows()
    ]

    return match_res, cc_unmatch_res, manual_unmatch_res
