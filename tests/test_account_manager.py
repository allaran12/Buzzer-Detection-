import unittest
from unittest.mock import AsyncMock, patch

from services.inference_api.account_manager import ScraperAccountManager


class AccountValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_complete_cookie_credentials(self):
        manager = ScraperAccountManager("/tmp/test-accounts.db")
        with patch("services.inference_api.account_manager.API") as api_cls:
            api = api_cls.return_value
            api.pool.delete_accounts = AsyncMock()
            api.pool.add_account = AsyncMock()
            api.pool.login_all = AsyncMock(return_value={"success": 1})
            api.pool.get_account = AsyncMock()
            api.pool.accounts_info = AsyncMock(return_value=[])
            result = await manager.add_and_login("cookie-user", "", "", "", "auth", "ct0")
        self.assertIn("result", result)
        api.pool.add_account.assert_awaited_once()
        api.pool.login_all.assert_awaited_once()

    async def test_accepts_complete_password_credentials_without_cookies(self):
        manager = ScraperAccountManager("/tmp/test-accounts.db")
        with patch("services.inference_api.account_manager.API") as api_cls:
            api = api_cls.return_value
            api.pool.delete_accounts = AsyncMock()
            api.pool.add_account = AsyncMock()
            api.pool.login_all = AsyncMock(return_value={"success": 1})
            api.pool.get_account = AsyncMock()
            api.pool.accounts_info = AsyncMock(return_value=[])
            result = await manager.add_and_login("password-user", "password", "email", "email-password", "", "")
        self.assertEqual(result["result"], {"success": 1})
        api.pool.login_all.assert_awaited_once()

    async def test_rejects_partial_credentials(self):
        manager = ScraperAccountManager("/tmp/test-accounts.db")
        with self.assertRaises(ValueError):
            await manager.add_and_login("partial-user", "", "", "", "auth", "")


if __name__ == "__main__":
    unittest.main()
