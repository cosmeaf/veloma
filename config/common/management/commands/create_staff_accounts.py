import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from config.authentication.services import FirstAccessService

# Departmental mailboxes of the office. `veloma` and `adm` lead the practice and
# get STAFF_MANAGER; the rest are STAFF. Adjust with --manager if that changes.
ACCOUNTS = (
    ('veloma@velomacontabilidade.com', 'Veloma', 'Contabilidade'),
    ('adm@velomacontabilidade.com', 'Administração', 'Veloma'),
    ('geral@velomacontabilidade.com', 'Geral', 'Veloma'),
    ('info@velomacontabilidade.com', 'Informações', 'Veloma'),
    ('cs@velomacontabilidade.com', 'Apoio ao Cliente', 'Veloma'),
    ('financeiro@velomacontabilidade.com', 'Financeiro', 'Veloma'),
    ('contabilidade@velomacontabilidade.com', 'Contabilidade', 'Veloma'),
    ('rh@velomacontabilidade.com', 'Recursos Humanos', 'Veloma'),
    ('suporte@velomacontabilidade.com', 'Suporte', 'Veloma'),
    ('ls@velomacontabilidade.com', 'LS', 'Veloma'),
    ('pv@velomacontabilidade.com', 'PV', 'Veloma'),
)

DEFAULT_MANAGERS = ('veloma@velomacontabilidade.com', 'adm@velomacontabilidade.com')


class Command(BaseCommand):
    help = (
        'Creates the office staff accounts with a temporary shared password. '
        'Each account must set its own email and password on first access.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=os.getenv('STAFF_INITIAL_PASSWORD', ''),
            help='Temporary password. Falls back to STAFF_INITIAL_PASSWORD.',
        )
        parser.add_argument(
            '--manager',
            default=','.join(DEFAULT_MANAGERS),
            help='Comma-separated emails that belong to STAFF_MANAGER.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reapply the temporary password and require first access again.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        if not password:
            self.stderr.write('A temporary password is required (--password or STAFF_INITIAL_PASSWORD).')
            return

        managers = {item.strip().lower() for item in options['manager'].split(',') if item.strip()}
        staff_group, _ = Group.objects.get_or_create(name='STAFF')
        manager_group, _ = Group.objects.get_or_create(name='STAFF_MANAGER')

        created, updated, skipped = 0, 0, 0
        for email, first_name, last_name in ACCOUNTS:
            email = email.strip().lower()
            user = User.objects.filter(username__iexact=email).first()

            if user and not options['reset']:
                skipped += 1
                self.stdout.write(f'  = {email} (já existe)')
                continue

            if user is None:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                )
                created += 1
                mark = '+'
            else:
                updated += 1
                mark = '~'

            user.set_password(password)
            user.is_active = True
            # These are portal accounts, never Django Admin accounts.
            user.is_staff = False
            user.is_superuser = False
            user.save()

            group = manager_group if email in managers else staff_group
            user.groups.add(group)
            FirstAccessService.require(user)
            self.stdout.write(f'  {mark} {email} · {group.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Contas: {created} criadas, {updated} atualizadas, {skipped} inalteradas. '
                'Todas exigem troca de e-mail e palavra-passe no primeiro acesso.'
            )
        )
