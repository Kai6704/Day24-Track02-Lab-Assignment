# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """

    # --- TASK 2.2.1 ---
    # CCCD: Hỗ trợ cả CMND (9 số) và CCCD (12 số), có thể nằm liền hoặc có khoảng trắng
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"\b\d{9,12}\b",          
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[cccd_pattern]
    )

    # --- TASK 2.2.2 ---
    # Số điện thoại: Bao phủ các trường hợp có dấu chấm, khoảng trắng, gạch ngang và +84
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_phone_broad",
            regex=r"(?:\+84|0)[0-9\-\.\s]{8,13}", 
            score=0.85
        )]
    )

    # Email: Bổ sung tường minh để tránh việc model bỏ sót
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        supported_language="vi",
        patterns=[Pattern("email_pattern", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", 0.9)]
    )

    # --- TASK 2.2.3 ---
    # Cấu hình NLP
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "vi", "model_name": "vi_core_news_lg"}],
        "ner_model_configuration": {
            "labels_to_ignore": ["O"],
            "model_to_presidio_entity_mapping": {
                "PER": "PERSON",
                "PERSON": "PERSON"
            }
        }
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["vi"])
    analyzer.registry.add_recognizer(cccd_recognizer)   
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)

    # Fallback cho Tên người: Regex không phân biệt hoa thường (?i), bắt các cụm 2 chữ trở lên
    name_regex = r"(?i)\b[a-zđàáâãèéêìíòóôõùúăđĩũơưăạảấầẩẫậắằẳẵặẹẻẽềềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]+\s[a-zđàáâãèéêìíòóôõùúăđĩũơưăạảấầẩẫậắằẳẵặẹẻẽềềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ\s]+\b"
    name_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(name="vn_name_broad", regex=name_regex, score=0.85)]
    )
    analyzer.registry.add_recognizer(name_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    """
    results = analyzer.analyze(
        text=text,       
        language="vi",   
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
        score_threshold=0.1  # <-- QUAN TRỌNG: Hạ threshold để chấp nhận các kết quả từ Regex dự phòng
    )
    return results