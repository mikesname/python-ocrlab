"""
Import a script file or files into the database.
"""

import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.utils import simplejson as json
from ocrlab import models


class Command(BaseCommand):
    args = "<scriptfile1> ... <scriptfileN>"
    help = "Import JSON scripts into the presets database"
    option_list = BaseCommand.option_list + (
        make_option(
            "-d",
            "--description",
            action="store",
            type="string",
            dest="description",
            default="",
            help="Description for the given preset"),
        make_option(
            "-n",
            "--name",
            action="store",
            type="string",
            dest="name",
            help="Name of the preset.  If not given, inferred from the file name"),
        make_option(
            "-t",
            "--tags",
            action="store",
            type="string",
            dest="tags",
            default="",
            help="Comma separated list of tags"),
        )

    def handle(self, *args, **options):
        try:
            adminuser = User.objects.get(is_superuser=True)
        except User.DoesNotExist:
            raise ImproperlyConfigured(
                    "An admin user must exist before presets can be imported.")

        if not args:
            raise CommandError("Scripts to import must be given as arguments.")
        for f in args:
            if not os.path.exists(f):
                raise CommandError("Script file does not exist: %s" % f)
            name = options.get("name")
            if name is None:
                name = os.path.splitext(os.path.basename(f))[0].capitalize()
            if name.strip() == "":
                raise CommandError("Script must have a valid name")
            tags = [t.strip() for t in options.get("tags", "").split(",")]
            description = options.get("description")
            with open(f) as fh:
                data = fh.read()
                try:
                    script = json.loads(data)
                    meta = script.get("__meta")
                    if meta is not None:
                        name = meta.get("name", name)
                        description = meta.get("description", options.get("description"))
                        tags = meta.get("tags", tags)
                except json.JSONDecodeError, err:
                    raise CommandError("Invalid script: JSON data could not be decoded.")
                p = models.Preset(name=name, description=description, data=data)
                p.save()
                p.tags.add(*tags)
            self.stdout.write("Successfully import preset: %s\n" % name)



