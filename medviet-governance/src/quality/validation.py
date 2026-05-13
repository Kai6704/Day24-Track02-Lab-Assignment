# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    # Lấy validator
    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(
        column="cccd",
        value=12
    )

    # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$" 
    )

    # 6. Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    # Tải data gốc để đối chiếu
    try:
        raw_df = pd.read_csv("data/raw/patients_raw.csv")
    except FileNotFoundError:
        raw_df = pd.DataFrame() # Fallback nếu không tìm thấy file raw

    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc 
    # (So sánh trực tiếp cột cccd của file ẩn danh với file raw, nếu giống nhau tức là chưa ẩn danh)
    if not raw_df.empty and 'cccd' in df.columns and 'cccd' in raw_df.columns:
        if df['cccd'].equals(raw_df['cccd']):
            results["success"] = False
            results["failed_checks"].append("Data Leakage: Cột CCCD chưa được ẩn danh (giống hệt dữ liệu gốc).")

    # Check 2: Không có null values trong các cột quan trọng
    important_columns = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in important_columns:
        if col in df.columns and df[col].isnull().any():
            results["success"] = False
            results["failed_checks"].append(f"Data Quality: Cột '{col}' chứa giá trị Null.")

    # Check 3: Số rows phải bằng original
    if not raw_df.empty:
        if len(df) != len(raw_df):
            results["success"] = False
            results["failed_checks"].append(
                f"Data Loss: Số lượng dòng không khớp. Gốc: {len(raw_df)}, Ẩn danh: {len(df)}."
            )

    return results