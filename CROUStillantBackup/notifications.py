import asyncio

from discord import Webhook, Embed
from aiohttp import ClientSession
from os import environ
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


class Notifications:
    def __init__(self):
        pass


    async def send(self, message: str) -> None:
        """
        Envoie un message sur le webhook

        :param message: Message à envoyer
        """
        session = ClientSession()
        webhook = Webhook.from_url(environ.get("WEBHOOK_URL"), session=session)

        embed = Embed(
            title="CROUStillant Backup",
            description=message,
            color=int(environ.get("COLOUR"), base=16),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"CROUStillant Développement © 2022 - {datetime.now(timezone("Europe/Paris")).year} | Tous droits réservés")
        embed.set_image(url="https://croustillant.bayfield.dev/banner-small.png")
        
        await webhook.send(embed=embed)
        
        await session.close()


    def run(self, message: str) -> None:
        """
        Envoie un message sur le webhook

        :param message: Message à envoyer
        """
        asyncio.run(self.send(message))
