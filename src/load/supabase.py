import logging

import aiohttp
import pandas as pd

from src.config import settings

log = logging.getLogger(__name__)


class SupabaseFundsRepository:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    def _validate_settings() -> None:
        if settings.SUPABASE_URL == "https://YOUR-PROJECT.supabase.co":
            raise ValueError("Configure SUPABASE_URL before running the scraper.")

        if settings.SUPABASE_SERVICE_ROLE_KEY == "EDIT_ME":
            raise ValueError(
                "Configure SUPABASE_SERVICE_ROLE_KEY before running the scraper."
            )

    @staticmethod
    def _headers() -> dict:
        return {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Accept-Profile": settings.SUPABASE_SCHEMA,
            "Content-Profile": settings.SUPABASE_SCHEMA,
            "Prefer": "return=minimal",
        }

    @staticmethod
    def _table_url() -> str:
        base_url = settings.SUPABASE_URL.rstrip("/")
        return f"{base_url}/rest/v1/{settings.SUPABASE_FUNDS_TABLE}"

    @staticmethod
    def _dataframe_to_records(df: pd.DataFrame) -> list[dict]:
        serialized_df = df.astype(object).where(pd.notna(df), None)
        return serialized_df.to_dict(orient="records")

    async def replace_funds(self, df: pd.DataFrame) -> None:
        self._validate_settings()

        if df is None or df.empty:
            raise ValueError("Cannot upload an empty DataFrame to Supabase.")

        await self._ensure_session()
        table_url = self._table_url()
        headers = self._headers()
        records = self._dataframe_to_records(df)

        log.info("[Funds List] Clearing Supabase table '%s'", settings.SUPABASE_FUNDS_TABLE)
        async with self.session.delete(table_url, headers=headers) as response:
            response_text = await response.text()
            if response.status >= 400:
                raise RuntimeError(
                    "Failed to clear Supabase table "
                    f"({response.status}): {response_text}"
                )

        batch_size = settings.SUPABASE_INSERT_BATCH_SIZE
        total_batches = (len(records) + batch_size - 1) // batch_size

        for batch_index, start in enumerate(range(0, len(records), batch_size), start=1):
            batch_records = records[start : start + batch_size]
            log.info(
                "[Funds List] Inserting batch %s/%s into Supabase (%s rows)",
                batch_index,
                total_batches,
                len(batch_records),
            )
            async with self.session.post(
                table_url,
                headers=headers,
                json=batch_records,
            ) as response:
                response_text = await response.text()
                if response.status >= 400:
                    raise RuntimeError(
                        "Failed to insert records into Supabase "
                        f"({response.status}): {response_text}"
                    )
