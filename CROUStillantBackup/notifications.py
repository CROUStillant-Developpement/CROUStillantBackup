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
        self.session = None
        self.webhook = None


    async def send(self, message: str) -> None:
        """
        Envoie un message sur le webhook

        :param message: Message à envoyer
        """
        if not self.session:
            self.session = ClientSession()
            self.webhook = Webhook.from_url(environ.get("WEBHOOK_URL"), session=self.session)

        embed = Embed(
            title="CROUStillant Backup",
            description=message,
            color=environ.get("COLOUR"),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"CROUStillant Développement © 2022 - {datetime.now(timezone("Europe/Paris")).year} | Tous droits réservés")
        embed.set_image(url="https://croustillant.bayfield.dev/banner-small.png")
        
        await self.webhook.send(embed=embed)


    def run(self, message: str) -> None:
        """
        Envoie un message sur le webhook

        :param message: Message à envoyer
        """
        asyncio.run(self.send(message))
