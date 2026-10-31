from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from bot.config import settings

SCHEMA = "gmail_checker"

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: Optional[str] = None,
    is_premium: bool = False,
) -> Dict[str, Any]:
    result = (
        supabase.schema(SCHEMA)
        .table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if result.data:
        user = result.data[0]
        update_data = {
            k: v
            for k, v in {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": language_code,
                "is_premium": is_premium,
            }.items()
            if v is not None
        }
        if update_data:
            supabase.schema(SCHEMA).table("users").update(update_data).eq(
                "id", user["id"]
            ).execute()
            user.update(update_data)
        return user

    insert_data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "language_code": language_code,
        "is_premium": is_premium,
    }
    result = (
        supabase.schema(SCHEMA)
        .table("users")
        .insert(insert_data)
        .execute()
    )
    return result.data[0]


async def create_order(
    user_id: str,
    order_type: str,
    accounts: List[Dict[str, str]],
    status_message: str = "Заказ принят",
    estimated_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    order_data = {
        "user_id": user_id,
        "type": order_type,
        "accounts_count": len(accounts),
        "status": "pending",
        "status_message": status_message,
        "estimated_minutes": estimated_minutes,
    }
    order_res = (
        supabase.schema(SCHEMA)
        .table("orders")
        .insert(order_data)
        .execute()
    )
    order = order_res.data[0]

    items = [
        {
            "order_id": order["id"],
            "login": acc["login"],
            "password": acc["password"],
            "status": "pending",
        }
        for acc in accounts
    ]
    if items:
        supabase.schema(SCHEMA).table("order_items").insert(items).execute()

    return order


async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    result = (
        supabase.schema(SCHEMA)
        .table("orders")
        .select("*")
        .eq("id", order_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_user_orders(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    result = (
        supabase.schema(SCHEMA)
        .table("orders")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


async def get_queue_stats() -> Dict[str, Any]:
    pending = (
        supabase.schema(SCHEMA)
        .table("orders")
        .select("id", count="exact")
        .in_("status", ["pending", "queued"])
        .execute()
    )
    processing = (
        supabase.schema(SCHEMA)
        .table("orders")
        .select("id", count="exact")
        .eq("status", "processing")
        .execute()
    )
    return {
        "pending_count": pending.count or 0,
        "processing_count": processing.count or 0,
    }


async def cancel_last_order(user_id: str) -> Optional[Dict[str, Any]]:
    result = (
        supabase.schema(SCHEMA)
        .table("orders")
        .select("*")
        .eq("user_id", user_id)
        .in_("status", ["pending", "queued"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    order = result.data[0]
    supabase.schema(SCHEMA).table("orders").update(
        {"status": "cancelled", "status_message": "Отменён пользователем"}
    ).eq("id", order["id"]).execute()

    order["status"] = "cancelled"
    return order
