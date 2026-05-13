package medviet.data_access

import future.keywords.if
import future.keywords.in

# Default: deny all
default allow := false

# Admin được phép tất cả
allow if {
    input.user.role == "admin"
}

# ML Engineer được đọc training data và model artifacts
allow if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts"}
    input.action in {"read", "write"}
}

# ML Engineer KHÔNG được delete production data
deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

# TODO: Data Analyst chỉ được đọc aggregated metrics và viết reports
allow if {
    input.user.role == "data_analyst"
    input.resource in {"aggregated_metrics", "reports"}
    
    # Logic: Chỉ được 'read' metrics, nhưng được 'read/write' cho reports
    is_valid_action(input.resource, input.action)
}

# Hàm bổ trợ để kiểm soát hành động chi tiết cho Data Analyst
# Sửa lại hàm bổ trợ để tuân thủ cú pháp mới
is_valid_action("aggregated_metrics", action) if { 
    action == "read" 
}

is_valid_action("reports", action) if { 
    action in {"read", "write"} 
}

# TODO: Intern chỉ được access sandbox
allow if {
    input.user.role == "intern"
    input.resource == "sandbox"
    # Giới hạn hành động để đảm bảo an toàn, ví dụ không cho delete
    input.action in {"read", "write"} 
}

# Rule: không ai được export restricted data ra ngoài VN servers
deny if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}