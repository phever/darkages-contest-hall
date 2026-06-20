import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import User, Contest, Entry, WorkflowStep

DATA_FILE = Path(__file__).resolve().parents[2] / 'data' / 'archive_entries.json'

BOARD_TITLE = "Active & Recent Contest Submissions"

INFO_MESSAGE = (
    "Reviews by nobles for the submissions listed here can be read on the board in "
    "the Mileth College Contest Hall. Unless one is spending three education marks to "
    "submit a work, clave recognition or higher is required to otherwise enter the "
    "Contest Hall. If you received a 'No Award' recommendation and would like to see "
    "the reviews for your submission, please reach out to a College Chancellor for "
    "assistance."
)

WORKFLOW_STEPS = [
    (1, "Submission",
     "The entrant has submitted their entry to the Mileth College."),
    (2, "Review",
     "The entry has been accepted by a College Chancellor and opened for review. "
     "The Chancellor becomes the review overseer. During this step nobles with "
     "village or greater recognition may review the entry and make recommendations "
     "for recognition level (or alternatively, recommend no recognition). The review "
     "period length is at the discretion of the overseeing Chancellor. Typically a "
     "minimum of three valid reviews must be received before the Chancellor will "
     "close the entry for review."),
    (3, "Loures Confirmation",
     "If the nobles recommended recognition, the results of the review shall be "
     "submitted by the overseeing Chancellor to the Library of Loures ((Kru)) for "
     "final approval. ((Note: College Chancellors have no special line of "
     "communication to Kru. We must submit tickets like everyone else; once we submit "
     "a ticket with a review recommendation to Kru, it is out of our hands when final "
     "confirmation comes.))"),
    (4, "Nobility Awarded",
     "The Library of Loures has formally recognized the submission and awarded the "
     "aisling with nobility."),
]


class Command(BaseCommand):
    help = "Seed the Contest Hall board: workflow steps, the archived works, and demo users."

    def add_arguments(self, parser):
        parser.add_argument(
            '--fresh', action='store_true',
            help="Delete existing entries on the board before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Workflow steps
        for number, title, description in WORKFLOW_STEPS:
            WorkflowStep.objects.update_or_create(
                number=number,
                defaults={'title': title, 'description': description},
            )
        self.stdout.write(self.style.SUCCESS(f"Workflow steps: {WorkflowStep.objects.count()}"))

        # 2. Board contest
        contest, _ = Contest.objects.get_or_create(
            title=BOARD_TITLE,
            defaults={'info_message': INFO_MESSAGE, 'is_active': True},
        )
        if contest.info_message != INFO_MESSAGE:
            contest.info_message = INFO_MESSAGE
            contest.save(update_fields=['info_message'])

        # 3. Archived works
        if options['fresh']:
            contest.entries.all().delete()

        data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        created = 0
        for row in data:
            _, was_created = Entry.objects.get_or_create(
                contest=contest,
                entrant_name=row['entrant_name'],
                work_title=row['work_title'],
                defaults={
                    'work_subject': row.get('work_subject', 'Other'),
                    'original_location_url': row.get('original_location_url', ''),
                    'original_location_label': row.get('original_location_label', ''),
                    'archived_location_url': row.get('archived_location_url', ''),
                    'review_overseer': row.get('review_overseer', ''),
                    'review_opened': row.get('review_opened', ''),
                    'review_closed': row.get('review_closed', ''),
                    'recommendation': row.get('recommendation', ''),
                    'current_step': row.get('current_step', 1),
                    'step_status': row.get('step_status', 'Submission'),
                },
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"Entries imported: {created} new, {contest.entries.count()} total on the board."
        ))

        # 4. Demo users
        if not User.objects.filter(username='chancellor').exists():
            User.objects.create_superuser(
                username='chancellor', email='chancellor@example.com', password='chancellor',
                role='admin', is_verified=True, in_game_name='Laurier',
            )
            self.stdout.write(self.style.SUCCESS("Created Chancellor superuser (chancellor / chancellor)."))

        if not User.objects.filter(username='noble').exists():
            User.objects.create_user(
                username='noble', email='noble@example.com', password='noblepass',
                role='voter', is_verified=True, in_game_name='Mayheart',
            )
            self.stdout.write(self.style.SUCCESS("Created verified voter (noble / noblepass)."))

        self.stdout.write(self.style.SUCCESS("Board seeded."))
