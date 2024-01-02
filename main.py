import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
import ssl
import sys
import argparse

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class ExchangeRate:
    def __init__(self):
        self.URL = "https://api.privatbank.ua/p24api/exchange_rates?date="
        self.exchange_rates = []

    async def get_currency_rates(self, date: datetime, currencies):
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            try:
                url = f"{self.URL}{date.strftime('%d.%m.%Y')}"
                async with session.get(url) as response:
                    data = await response.json()
                    # print(f"Date: {date.strftime('%Y-%m-%d')}, Currency Rates: {data}")
                    currency_rates = {
                        date.strftime("%d.%m.%Y"): {
                            currency["currency"]: {
                                "sale": currency["saleRate"],
                                "purchase": currency["purchaseRate"],
                            }
                            for currency in data["exchangeRate"]
                            if currency["currency"] in currencies
                        }
                    }
                    self.exchange_rates.append(currency_rates)
            except aiohttp.ClientError as e:
                print(f"HTTP error occurred: {e}")
            except Exception as e:
                print(f"Error occurred: {e}")

    async def fetch_last_n_days(self, n_days, currencies):
        today = datetime.today()
        for i in range(1, n_days + 1):
            date = today - timedelta(days=i)
            await self.get_currency_rates(date, currencies)

    async def save_to_json(self):
        with open("currency.json", "w") as file:
            json.dump(self.exchange_rates, file, indent=2)


async def main():
    parser = argparse.ArgumentParser(
        description="Retrieve currency rates for the last N days"
    )
    parser.add_argument("days", type=int, help="Number of days")
    parser.add_argument(
        "-c",
        "--currencies",
        nargs="+",
        default=["USD", "EUR"],
        help="Additional currencies",
    )
    args = parser.parse_args()

    if args.days > 10:
        print("Error: Number of days should not exceed 10")
        sys.exit(1)

    exchange_rate = ExchangeRate()
    await exchange_rate.fetch_last_n_days(args.days, args.currencies)
    await exchange_rate.save_to_json()


if __name__ == "__main__":
    asyncio.run(main())
