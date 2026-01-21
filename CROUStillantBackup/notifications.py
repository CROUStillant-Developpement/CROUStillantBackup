import asyncio


from .utils.views import WorkerView
from discord import Webhook
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
        webhook = Webhook.from_url(environ.get("BACKUP_WEBHOOK_URL"), session=session)

        view = WorkerView(
            content=f"## CROUStillant Backup\n\n{message}",
            thumbnail_url="https://croustillant.menu/logo.png",
            banner_url="https://croustillant.menu/banner-small.png",
            footer_text=f"CROUStillant Développement © 2022 - {datetime.now(timezone("Europe/Paris")).year} | Tous droits réservés."
        )

        await webhook.send(view=view)

        await session.close()


    def run(self, message: str) -> None:
        """
        Envoie un message sur le webhook

        :param message: Message à envoyer
        """
        asyncio.run(self.send(message))
