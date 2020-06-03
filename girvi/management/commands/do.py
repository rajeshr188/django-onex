from django.core.management.base import BaseCommand,CommandError
from django.apps import apps
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from girvi.models import License,Loan,Release
from datetime import datetime,timezone

CREATE = 'create'
LIST = 'list'
UPDATE = 'update'
DELETE = 'delete'
LICENSE = 'license'
LOAN = 'loan'
RELEASE = 'release'
ADJUSTMENTS = 'adjustment'
INFO = '-i',


class Command(BaseCommand):
    help ='Operations on models in Girvi app'

    def add_arguments(self,parser):

        parser.add_argument(
            'operation',
            choices=(
            CREATE,
            DELETE,
            UPDATE,
            LIST,
            )
        )
        parser.add_argument(
            'model',
            choices = (
            LICENSE,
            LOAN,
            RELEASE,
            ADJUSTMENTS,
            )
        )
        parser.add_argument(
            'id', nargs = '+', type =str
        )


    def get_model(self,model):
        return apps.get_model(
            app_label='girvi',
            model_name = model
            )

    def create(self,model,id):
        model_class = self.get_model(model)
        for loan in id:
            try:
                l = Loan.objects.get(loanid=loan)

            except Loan.DoesNotExist:
                    raise CommandError(f"Failed to create Release as {loan} does not exist")
            try:
                releaseid = Release.objects.order_by('-id')[0]
                releaseid = str(int(releaseid.releaseid)+1)
                r = Release.objects.create(releaseid=releaseid,loan=l,created = datetime.now(timezone.utc),interestpaid =  l.interestdue())
                self.stdout.write(self.style.SUCCESS(f"Successfully closed Loan:{l} with Release id: {r}"))
            except IntegrityError:
                raise CommandError(f"Failed creating Release as {l} is already Released with {l.release}")

    def delete(self,model,ids = None):
        model_class = self.get_model(model)
        if id:
            for item in ids:
                model_class.objects.get(id=item).delete()

    def update(self,model):
        pass

    def list(self,model,ids=None):
        model_class = self.get_model(model)
        if ids:
            for item in ids:
                row = get_object_or_404(model_class,id = int(item))
                self.stdout.write(f"{model} {row.id} {row.created} ")


    def handle(self,*args,**options):

        op = options.get('operation')
        model = options.get('model')
        id = options.get('id')

        if op == CREATE:
            if model in (LOAN,LICENSE,ADJUSTMENTS):
                self.stdout.write("Work in Progress")
            else:
                self.stdout.write("creating Release...")
                self.create(model,id)

        if op == LIST:
            self.list(model,id)

        if op in (CREATE, LIST, UPDATE, DELETE):
            self.stdout.write(
                self.style.SUCCESS("Done! Success.")
            )





        # if options['--i']:
        #     for release in options['loanid']:
        #         try:
        #             self.stdout.write(f"Release id:{id} releaseid:{releaseid} loan:{loan} Paid Int:{interestpaid}")
        #         except Release.DoesNotExist:
        #             raise CommandError(f"release {release} doesnot exist")

        # for loan in options['loanid']:
        #
        #     self.stdout.write(self.style.SUCCESS(f"Successfully closed loan {loan} with Release {r}"))
