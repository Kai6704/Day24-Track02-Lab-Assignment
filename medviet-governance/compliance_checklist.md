# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có (OPA policy deny export khi destination_country != "VN")

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure — endpoint DELETE /api/patients/{patient_id}, chỉ admin thực thi)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach (Prometheus + Grafana trong docker-compose.yml)
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM at rest (SimpleVault — envelope encryption), TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | Mỗi API request ghi lại `accessed_by` (username); tích hợp Prometheus metrics theo dõi access pattern | ✅ Done | Platform Team |
| Breach detection | Prometheus scrape metrics từ FastAPI; Grafana alert khi spike 4xx/5xx vượt ngưỡng | ✅ Done | Security Team |

## F. Technical Solution cho các mục đã hoàn thành

### Audit Logging
**Giải pháp:** Mỗi endpoint trong `src/api/main.py` trả về trường `accessed_by` chứa username của người thực hiện request. Trong production, tích hợp thêm:
- **Structured logging** với `structlog` hoặc Python `logging` ghi ra stdout theo format JSON.
- Forward log sang Elasticsearch hoặc Loki (Grafana stack đã có trong `docker-compose.yml`).
- Log tối thiểu gồm: `timestamp`, `user`, `role`, `resource`, `action`, `ip_address`, `http_status`.

### Breach Detection
**Giải pháp:** Prometheus + Grafana đã được cấu hình trong `docker-compose.yml`:
- Prometheus scrape metrics từ FastAPI (expose `/metrics` qua `prometheus-fastapi-instrumentator`).
- Grafana tạo alert rule: nếu số lượng HTTP 401/403 trong 5 phút vượt ngưỡng → gửi cảnh báo qua email/Slack.
- Kết hợp với OPA policy (`deny` export data ra ngoài VN) để chặn data exfiltration tự động.
- Khi alert kích hoạt, team Security có 72h để điều tra và báo cáo theo NĐ13/2023 Điều 23.
