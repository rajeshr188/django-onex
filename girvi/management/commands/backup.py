# backup_postgres.py

import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

# class Command(BaseCommand):
#     help = 'Backup PostgreSQL data'

#     def handle(self, *args, **options):
#         database_name = settings.DATABASES['default']['NAME']
#         user = settings.DATABASES['default']['USER']
#         password = settings.DATABASES['default']['PASSWORD']
#         host = settings.DATABASES['default']['HOST']
#         port = settings.DATABASES['default']['PORT']

#         backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
#         backup_file = f'backup_{database_name}_{backup_date}.sql'

#         # Construct the PostgreSQL dump command
#         dump_cmd = [
#             'pg_dump',
#             '-h', host,
#             '-p', str(port),
#             '-U', user,
#             '-P',password,
#             '-F', 'c',  # Custom format
#             '-b',  # Include blobs
#             '-f', backup_file,
#             database_name,
#         ]

#         # If a password is set, include it in the command
#         if password:
#             dump_cmd.extend(['-W', password])

#         try:
#             # Execute the PostgreSQL dump command
#             subprocess.run(dump_cmd, check=True)
#             self.stdout.write(self.style.SUCCESS(f'Successfully backed up {database_name} to {backup_file}'))
#         except subprocess.CalledProcessError as e:
#             self.stderr.write(self.style.ERROR(f'Error during backup: {e}'))
#         finally:
#             # Clean up the backup file
#             if os.path.exists(backup_file):
#                 os.remove(backup_file)


class Command(BaseCommand):
    help = "Backup PostgreSQL database"

    def handle(self, *args, **options):
        # Define your PostgreSQL database settings
        db_settings = settings.DATABASES["default"]

        # # Create backup directory if it doesn't exist
        # backup_dir = 'path/to/your/backup/directory'
        # os.makedirs(backup_dir, exist_ok=True)
        # Create backup directory within your Django project if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, "backup")
        os.makedirs(backup_dir, exist_ok=True)

        # Backup filename with timestamp
        backup_file = os.path.join(
            backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        )

        # Set the PGPASSWORD environment variable with the database user's password
        os.environ["PGPASSWORD"] = db_settings["PASSWORD"]
        # PostgreSQL dump command
        dump_cmd = f"pg_dump -h {db_settings['HOST']} -d {db_settings['NAME']} -U {db_settings['USER']} -Fc -f {backup_file}"

        # Execute the command
        os.system(dump_cmd)

        self.stdout.write(
            self.style.SUCCESS(f"Database backup created at {backup_file}")
        )
