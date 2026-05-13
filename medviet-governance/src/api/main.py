# src/api/main.py
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# Đường dẫn mặc định đến file dữ liệu
DATA_PATH = "data/raw/patients_raw.csv"

def load_data() -> pd.DataFrame:
    """Helper function đọc CSV và xử lý NaN để tránh lỗi khi parse JSON."""
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Data file not found")
    df = pd.read_csv(DATA_PATH)
    # Thay thế NaN bằng chuỗi rỗng để FastAPI có thể parse JSON thành công
    return df.fillna("")

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = load_data()
    # Lấy 10 dòng đầu tiên và chuyển thành list of dicts
    records = df.head(10).to_dict(orient="records")
    return {"data": records, "accessed_by": current_user["username"]}

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = load_data()
    df_top10 = df.head(10)
    # Chạy qua pipeline ẩn danh
    df_anon = anonymizer.anonymize_dataframe(df_top10)
    records = df_anon.to_dict(orient="records")
    return {"data": records, "accessed_by": current_user["username"]}

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = load_data()
    # Gom nhóm và đếm số lượng bệnh nhân theo từng loại bệnh
    disease_counts = df["benh"].value_counts().to_dict()
    
    return {
        "metrics": {
            "total_patients": len(df),
            "patient_count_by_disease": disease_counts
        },
        "accessed_by": current_user["username"]
    }

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    # Trong môi trường thực tế, đây là nơi thực thi logic xóa trên DB
    return {
        "message": f"Patient {patient_id} has been deleted successfully.",
        "deleted_by": current_user["username"]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}