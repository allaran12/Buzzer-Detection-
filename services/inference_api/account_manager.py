from __future__ import annotations

import os
from pathlib import Path

from twscrape import API


class ScraperAccountManager:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    async def status(self) -> list[dict]:
        api = API(self.db_path)
        accounts = await api.pool.accounts_info()
        return [{**account, "logged_in": bool(account.get("active")), "error_msg": None if account.get("error_msg") in (None, "None") else account.get("error_msg")} for account in accounts]

    async def add_and_login(self, username: str, password: str, email: str, email_password: str, auth_token: str, ct0: str) -> dict:
        username = username.strip() or ("session_" + auth_token[:12])
        if not username:
            raise ValueError("username wajib diisi untuk login password")
        has_cookies = bool(auth_token.strip()) and bool(ct0.strip())
        has_password_credentials = all(value.strip() for value in (password, email, email_password))
        if not has_cookies and not has_password_credentials:
            raise ValueError("Isi auth_token dan ct0, atau password, email, dan email_password")
        if bool(auth_token.strip()) != bool(ct0.strip()):
            raise ValueError("auth_token dan ct0 harus diisi bersamaan")
        api = API(self.db_path)
        await api.pool.delete_accounts(username)
        cookies = f"auth_token={auth_token.strip()}; ct0={ct0.strip()}" if has_cookies else None
        await api.pool.add_account(username, password, email, email_password, cookies=cookies)
        if cookies:
            result = await api.pool.login_all([username])
            account = await self._status_with_failure(api, username)
            return {"result": result, "account": account}
        result = await api.pool.login_all([username])
        account = await self._status_with_failure(api, username)
        return {"result": result, "account": account}

    async def login(self, username: str) -> dict:
        api = API(self.db_path)
        result = await api.pool.login_all([username])
        account = await self._status_with_failure(api, username)
        return {"result": result, "account": account}

    async def _status_with_failure(self, api: API, username: str) -> dict | None:
        account_obj = await api.pool.get_account(username)
        if account_obj is not None and not account_obj.active and not account_obj.error_msg:
            account_obj.error_msg = "Login gagal: X mengembalikan HTTP 403/Cloudflare. Gunakan session browser atau coba jaringan/IP berbeda."
            await api.pool.save(account_obj)
        items = await api.pool.accounts_info()
        return next((item for item in items if item["username"] == username), None)

    async def delete(self, username: str) -> None:
        api = API(self.db_path)
        await api.pool.delete_accounts(username)


def scraper_db_path(root: Path) -> Path:
    configured = os.getenv("COORDINX_SCRAPER_DB")
    path = Path(configured) if configured else root / "accounts.db"
    return path if path.is_absolute() else root / path
