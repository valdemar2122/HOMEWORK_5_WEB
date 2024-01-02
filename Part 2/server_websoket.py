import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from mains import ExchangeRate, json, datetime
from aiofile import async_open
from aiopath import AsyncPath

logging.basicConfig(level=logging.INFO)


async def handle_command(command):
    command_parts = command.split()
    if command_parts[0] == "exchange" and len(command_parts) == 2:
        try:
            days = int(command_parts[1])
            if days > 10:
                return "Error: Number of days should not exceed 10"

            # Initialize ExchangeRate class
            exchange_rate = ExchangeRate()

            # Fetch currency rates for the specified number of days for USD and EUR
            await exchange_rate.fetch_last_n_days(days, ["USD", "EUR"])

            # Load the JSON file containing the fetched currency rates
            with open("Part 2/currency.json", "r") as file:
                currency_rates = json.load(file)

            # Prepare the response message with the fetched currency rates
            response = json.dumps(currency_rates)

            # Log the executed command to a file
            async with async_open("commands.log", mode="a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await log_file.write(
                    f"Command 'exchange {days}' executed at {timestamp}\n"
                )

            return response
        except ValueError:
            return "Error: Invalid number of days. Please enter a valid integer."
    else:
        return "Unknown command"


async def consumer_handler(websocket, path):
    async for message in websocket:
        command = message.strip()  # Отримати команду від користувача
        response = await handle_command(command)  # Обробити команду
        await websocket.send(response)  # Надіслати відповідь користувачеві


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(consumer_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
