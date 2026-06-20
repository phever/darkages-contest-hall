import os
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Entry, VoteIntention

BOARD_URL = os.getenv('BOARD_URL', 'https://collegebeta.phever.dev')


def _build_email(entry, intention):
    user = intention.user
    closes = entry.review_closes_at.strftime('%Y-%m-%d')
    lines = [
        f"Hail {user.in_game_name or user.username},",
        "",
        f'The review period for "{entry.work_title}" by {entry.entrant_name} closes on {closes}. '
        "You asked to be reminded before voting ends in the Mileth College Contest Hall.",
        "",
    ]
    if intention.recommendation:
        lines += [f"Your intended recommendation: {intention.recommendation}", ""]
    if intention.review_text:
        lines += ["Your saved draft review (copy this into the in-game Contest Hall):", "",
                  intention.review_text, ""]
    lines += [f"View the board: {BOARD_URL}", "", "— Mileth College Contest Hall"]
    return f'Review closing soon: "{entry.work_title}"', "\n".join(lines)


class SendRemindersView(APIView):
    """
    Hit on a schedule by Vercel Cron. Emails nobles who opted into a reminder on
    entries whose review period is about to close. Idempotent: each intention is
    reminded at most once (reminder_sent_at).
    """
    authentication_classes = []  # cron uses a bearer secret, not JWT
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        secret = os.getenv('CRON_SECRET')
        if secret and request.headers.get('Authorization') != f'Bearer {secret}':
            return Response({'detail': 'Unauthorized'}, status=401)

        now = timezone.now()
        lead = timedelta(days=int(os.getenv('REMINDER_LEAD_DAYS', '3')))
        entries = Entry.objects.filter(
            review_closes_at__isnull=False,
            review_closes_at__gte=now,
            review_closes_at__lte=now + lead,
        ).exclude(current_step__gte=Entry.TOTAL_STEPS)

        sent, skipped = 0, 0
        for entry in entries:
            pending = entry.vote_intentions.filter(
                remind_before_close=True, reminder_sent_at__isnull=True,
            ).select_related('user')
            for intention in pending:
                if not intention.user.email:
                    skipped += 1
                    continue
                subject, body = _build_email(entry, intention)
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                          [intention.user.email], fail_silently=False)
                intention.reminder_sent_at = now
                intention.save(update_fields=['reminder_sent_at'])
                sent += 1

        return Response({
            'entries_closing_soon': entries.count(),
            'reminders_sent': sent,
            'skipped_no_email': skipped,
        })
