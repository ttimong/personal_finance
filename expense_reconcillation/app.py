import json

from constants import ManualColNamesMap, StmtColNamesMap
from flask import Flask, jsonify, request
from flask_cors import CORS
from helper import load_data, match_data

app = Flask(__name__)
CORS(app)


@app.route("/api/process", methods=["POST"])
def process_data():
    # Retrieve files from the request
    if "stmt_files" not in request.files:
        return jsonify({"error": "'stmt_file' is not in request object"}), 400

    stmt_files = request.files.getlist("stmt_files")
    if len(stmt_files) == 0:
        return jsonify({"error": "No statement files provided"}), 400

    if "manual_file" not in request.files:
        return jsonify({"error": "'manual_file' is not in request object"}), 400

    manual_file = request.files["manual_file"]
    if manual_file.filename == "":
        return jsonify({"error": "No manual tracking file provided"}), 400

    if not manual_file.filename.endswith(".csv"):
        return jsonify({"error": "The manual tracking file must be a CSV"}), 400

    # Retrieve custom column names from the request (if provided)
    custom_stmt_cols = request.form.get("stmt_cols")
    custom_manual_cols = request.form.get(
        "manual_cols"
    )  # e.g. {"manual_date": "datexxx"}
    try:
        stmt_col_map = StmtColNamesMap.copy()
        manual_col_map = ManualColNamesMap.copy()

        if custom_stmt_cols:
            custom_stmt_cols = json.loads(custom_stmt_cols)
            stmt_col_map.update(custom_stmt_cols)

        if custom_manual_cols:
            custom_manual_cols = json.loads(custom_manual_cols)
            manual_col_map.update(custom_manual_cols)
    except Exception as e:
        return jsonify({"error": f"Invalid custom column names: {str(e)}"}), 400

    # Process data
    try:
        stmt_df = load_data(stmt_files, stmt_col_map)
        manual_df = load_data([manual_file], manual_col_map)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    match_res, stmt_unmatch_res, manual_unmatch_res = match_data(
        stmt_df,
        manual_df,
    )

    return (
        jsonify(
            {
                "status": "success",
                "data": {
                    "match_data": match_res,
                    "stmt_unmatch_data": stmt_unmatch_res,
                    "manual_unmatch_data": manual_unmatch_res,
                },
                "message": "Data processed successfully",
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True)
