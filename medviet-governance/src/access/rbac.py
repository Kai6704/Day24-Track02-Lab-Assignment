# src/access/rbac.py
import casbin
from functools import wraps
from fastapi import HTTPException, Header
from typing import Optional

# Danh sách user giả lập (production dùng JWT + DB)
MOCK_USERS = {
    "token-alice": {"username": "alice", "role": "admin"},
    "token-bob":   {"username": "bob",   "role": "ml_engineer"},
    "token-carol": {"username": "carol", "role": "data_analyst"},
    "token-dave":  {"username": "dave",  "role": "intern"},
}

# Khởi tạo Casbin enforcer với model và policy đã định nghĩa
enforcer = casbin.Enforcer("src/access/model.conf", "src/access/policy.csv")

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Parse Bearer token và trả về user info.
    Raise HTTPException 401 nếu token không hợp lệ.
    """
    if not authorization or not authorization.startswith("Bearer "):
        # 401 Unauthorized: Bắt buộc xác thực danh tính
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ")[1]
    user = MOCK_USERS.get(token)

    if not user:
        # 401 Unauthorized: Token sai hoặc đã hết hạn
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

def require_permission(resource: str, action: str):
    """
    Decorator kiểm tra RBAC permission.
    Dùng casbin enforcer để check (username, resource, action).
    Raise HTTPException 403 nếu không có quyền.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Lấy current_user từ kwargs (FastAPI inject qua Depends)
            current_user = kwargs.get("current_user")
            
            if not current_user:
                raise HTTPException(status_code=401, detail="User not authenticated")

            role = current_user["role"]
            username = current_user["username"]

            # Dùng username thay vì role để Casbin tự map qua quy tắc 'g' (như g, alice, admin)
            allowed = enforcer.enforce(username, resource, action)  

            if not allowed:
                # 403 Forbidden: Đã biết là ai nhưng không cho phép truy cập
                raise HTTPException(
                    status_code=403,    
                    detail=f"Role '{role}' (User '{username}') cannot '{action}' on '{resource}'"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator