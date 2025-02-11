import datetime
import docker
import time

from .notifications import Notifications
from .utils.logger import Logger
from dotenv import load_dotenv
from os import path, environ, makedirs, listdir, remove, stat


load_dotenv(dotenv_path=".env")


class Backup:
    def __init__(self):
        self.logger = Logger("backup")

        self.container = environ.get("CONTAINER")
        self.db = environ.get("POSTGRES_DATABASE")
        self.user = environ.get("POSTGRES_USER")
        self.password = environ.get("POSTGRES_PASSWORD")
        self.backup_dir = environ.get("BACKUP_DIR")

        if not all([self.container, self.db, self.user, self.password, self.backup_dir]):
            self.logger.error("Des variables d'environnement requises sont manquantes. Vérifiez votre fichier .env.")
            raise ValueError("Missing required environment variables. Check your .env file.")

        self.daily_backup_dir = path.join(self.backup_dir, "daily")
        self.monthly_backup_dir = path.join(self.backup_dir, "monthly")

        makedirs(self.daily_backup_dir, exist_ok=True)
        makedirs(self.monthly_backup_dir, exist_ok=True)

        self.client = docker.from_env()
        
        self.notifications = Notifications()


    def runCommandInContainer(self, command: str, skip_error: bool = False) -> bool:
        """
        Lance une commande dans un conteneur Docker.
        
        :param command: Commande à exécuter
        :param skip_error: Ignorer les erreurs de commande
        :return: True si la commande a réussi, False sinon
        """
        try:
            container = self.client.containers.get(self.container)
            result = container.exec_run(command)

            if result.exit_code != 0:
                if skip_error:
                    return True
                else:
                    self.logger.error(f"La commande a échoué : {result.output.decode()}")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Une erreur s'est produite lors de l'exécution de la commande: {e}")
            return False


    def dailyBackup(self) -> None:
        """
        Effectue une sauvegarde quotidienne en utilisant pg_dump.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        backup_file = path.join(self.daily_backup_dir, f"{self.db}_daily_{timestamp}.sql.gz")

        self.logger.info(f"Lancement de la sauvegarde quotidienne pour {self.db}...")

        if self.runCommandInContainer(
            command=f"pg_dump -U {self.user} {self.db} -Z 9 -f /tmp/backup.sql.gz"
        ):
            container = self.client.containers.get(self.container)
            backup_data = container.get_archive("/tmp/backup.sql.gz")[0]

            with open(backup_file, "wb") as f:
                for chunk in backup_data:
                    f.write(chunk)

            self.logger.info(f"Sauvegarde quotidienne terminée : {backup_file}")
            self.notifications.run(f"Sauvegarde quotidienne terminée : `{self.db}_daily_{timestamp}.sql.gz`")
        else:
            self.logger.error("La sauvegarde quotidienne a échoué.")


    def monthlyBackup(self) -> None:
        """
        Effectue une sauvegarde mensuelle complète en utilisant pg_basebackup.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        backup_file = path.join(self.monthly_backup_dir, f"{self.db}_monthly_{timestamp}.tar.gz")

        self.logger.info(f"Lancement de la sauvegarde mensuelle complète pour {self.db}...")

        if self.runCommandInContainer(
            command=f"pg_basebackup -U {self.user} -Ft -X none -P -D /tmp/full_backup"
        ):
            container = self.client.containers.get(self.container)
            backup_data = container.get_archive("/tmp/full_backup/base.tar")[0]
            
            with open(backup_file, "wb") as f:
                for chunk in backup_data:
                    f.write(chunk)

            self.logger.info(f"Sauvegarde mensuelle terminée : {backup_file}")
            self.notifications.run(f"Sauvegarde mensuelle terminée : `{self.db}_monthly_{timestamp}.tar.gz`")
        else:
            self.logger.error("La sauvegarde mensuelle a échoué.")


    def cleanupOldBackups(self, directory: str, days: int = 7) -> None:
        """
        Supprime les fichiers plus anciens que `days` du répertoire spécifié.
        
        :param directory: Répertoire à nettoyer
        :param days: Nombre de jours à conserver
        """
        now = time.time()
        cutoff = now - (days * 86400)

        self.logger.info(f"Nettoyage des anciennes sauvegardes dans {directory}...")

        for filename in listdir(directory):
            file_path = path.join(directory, filename)

            if path.isfile(file_path):
                file_age = stat(file_path).st_mtime

                if file_age < cutoff:
                    try:
                        remove(file_path)

                        self.logger.info(f"Suppression de l'ancienne sauvegarde : {file_path}")
                        self.notifications.run(f"Suppression de l'ancienne sauvegarde : `{filename}`")
                    except Exception as e:
                        self.logger.error(f"Impossible de supprimer {file_path}: {e}")


    def cleanTempFiles(self) -> None:
        """
        Nettoie les fichiers temporaires dans le conteneur.
        """
        self.logger.info("Nettoyage des fichiers temporaires...")
        self.notifications.run("Nettoyage des fichiers temporaires...")

        # Vérifier si le fichier de sauvegarde quotidienne existe
        if self.runCommandInContainer(
            command="test -f /tmp/backup.sql.gz",
            skip_error=True
        ):
            self.runCommandInContainer(
                command="rm -f /tmp/backup.sql.gz",
                skip_error=True
            )

        # Vérifier si le fichier de sauvegarde mensuelle existe
        if self.runCommandInContainer(
            command="test -d /tmp/full_backup",
            skip_error=True
        ):
            self.runCommandInContainer(
                command="rm -rf /tmp/full_backup",
                skip_error=True
            )


    def run(self):
        """
        Lance le processus de sauvegarde.
        """
        self.notifications.run("Lancement du processus de sauvegarde...")

        today = datetime.date.today()

        # Nettoyer les fichiers temporaires
        self.cleanTempFiles()

        # Effectuer une sauvegarde quotidienne
        self.dailyBackup()

        # Vérifie si une sauvegarde mensuelle est déjà effectuée
        if not any(f.startswith(f"{self.db}_monthly") for f in listdir(self.monthly_backup_dir)):
            self.monthlyBackup()

        # Effectuer une sauvegarde mensuelle le premier jour du mois
        if today.day == 1:
            self.monthlyBackup()

        # Nettoyer les fichiers temporaires
        self.cleanTempFiles()

        # Nettoyer les anciennes sauvegardes
        self.cleanupOldBackups(self.daily_backup_dir, days=7)

        self.notifications.run("Processus de sauvegarde terminé.")
