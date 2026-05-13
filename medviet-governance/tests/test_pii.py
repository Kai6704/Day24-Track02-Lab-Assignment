# tests/test_pii.py
import pytest
import pandas as pd
from src.pii.anonymizer import MedVietAnonymizer

@pytest.fixture
def anonymizer():
    return MedVietAnonymizer()

@pytest.fixture
def sample_df():
    # Đảm bảo file csv tồn tại ở đường dẫn tương ứng khi chạy test
    return pd.read_csv("data/raw/patients_raw.csv").head(50)

class TestPIIDetection:

    def test_cccd_detected(self, anonymizer):
        text = "Bệnh nhân Nguyen Van A, CCCD: 012345678901"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                              entities=["VN_CCCD"])
        # Assert rằng có ít nhất 1 result
        assert len(results) > 0

    def test_phone_detected(self, anonymizer):
        text = "Liên hệ: 0912345678"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                              entities=["VN_PHONE"])
        # Assert tìm thấy số điện thoại
        assert len(results) > 0

    def test_email_detected(self, anonymizer):
        text = "Email: nguyenvana@gmail.com"
        results = anonymizer.analyzer.analyze(text=text, language="vi",
                                              entities=["EMAIL_ADDRESS"])
        # Assert tìm thấy email
        assert len(results) > 0

    # --- TASK QUAN TRỌNG ---
    def test_detection_rate_above_95_percent(self, anonymizer, sample_df):
        """Pipeline phải đạt >95% detection rate."""
        pii_columns = ["ho_ten", "cccd", "so_dien_thoai", "email"]
        rate = anonymizer.calculate_detection_rate(sample_df, pii_columns)
        print(f"\nDetection rate: {rate:.2%}")
        assert rate >= 0.95, f"Detection rate {rate:.2%} < 95%"

class TestAnonymization:

    def test_pii_not_in_output(self, anonymizer, sample_df):
        """Sau anonymization, không còn CCCD gốc trong output."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        
        # Lấy danh sách CCCD đã được làm ẩn để kiểm tra nhanh
        anon_cccd_values = df_anon["cccd"].astype(str).values
        
        for original_cccd in sample_df["cccd"]:
            # Bỏ qua nếu giá trị gốc là NaN
            if pd.isna(original_cccd):
                continue
            # Assert CCCD gốc không xuất hiện trong cột cccd của df_anon
            assert str(original_cccd) not in anon_cccd_values

    def test_non_pii_columns_unchanged(self, anonymizer, sample_df):
        """Cột benh và ket_qua_xet_nghiem phải giữ nguyên."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        
        # Sử dụng hàm assert có sẵn của Pandas để kiểm tra 2 Series có y hệt nhau không
        pd.testing.assert_series_equal(sample_df["benh"], df_anon["benh"])
        pd.testing.assert_series_equal(sample_df["ket_qua_xet_nghiem"], df_anon["ket_qua_xet_nghiem"])