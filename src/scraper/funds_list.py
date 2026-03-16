import asyncio
import logging

import pandas as pd

import src.etl.transform as transform
from src.config.constants import RequestConfig
from src.etl.extract import Extract
from src.load.supabase import SupabaseFundsRepository

log = logging.getLogger(__name__)


class FundsList:
    def __init__(self):
        self.extract = Extract()
        self.supabase_repository = SupabaseFundsRepository()

    async def run(self) -> None:
        try:
            df_funds = await self.get_df_funds()
            await self.process_funds(df_funds=df_funds)
        finally:
            await self.extract.close()
            await self.supabase_repository.close()

    async def get_df_funds(self) -> pd.DataFrame:
        log.info("[Funds List] Fetching data from the API")
        response = await self.extract.request_get(
            url=RequestConfig.URL_US_FUNDS, headers=RequestConfig.BASIC_HEADERS
        )
        response_data = response.json()
        df_funds = transform.parse_funds(response_data=response_data)

        return df_funds

    async def process_funds(self, df_funds: pd.DataFrame) -> None:
        log.info("[Funds List] Processing data into Supabase")
        await self.supabase_repository.replace_funds(df=df_funds)


async def main():
    log.info("[Funds List] Initializing BlackRock Funds List Scraper")

    scraper = FundsList()
    await scraper.run()

    log.info("[Funds List] BlackRock Funds List Scraper finished")


if __name__ == "__main__":
    asyncio.run(main())
