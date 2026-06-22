from rest_framework import status
from rest_framework.test import APITestCase

from .models import Contest, Entry, User


class AdvanceStepTests(APITestCase):
    def setUp(self):
        self.contest = Contest.objects.create(title='Mileth College Contest Hall')
        self.entry = Entry.objects.create(
            contest=self.contest, entrant_name='Aengus', work_title='On Loures',
            current_step=2, step_status='Review',
        )
        self.chancellor = User.objects.create_user(
            username='chancellor', password='x', role='admin', is_staff=True,
        )
        self.noble = User.objects.create_user(
            username='noble', password='x', role='voter', is_verified=True,
        )

    def url(self, entry=None):
        return f'/api/entries/{(entry or self.entry).id}/advance-step/'

    def test_chancellor_advances_one_step(self):
        self.client.force_authenticate(self.chancellor)
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['steps_complete'], 3)
        self.assertEqual(res.data['step_status'], 'Loures Confirmation')
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.current_step, 3)

    def test_advancing_final_step_is_rejected(self):
        self.entry.current_step = Entry.TOTAL_STEPS
        self.entry.step_status = 'Nobility Awarded'
        self.entry.save()
        self.client.force_authenticate(self.chancellor)
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.current_step, Entry.TOTAL_STEPS)

    def test_noble_cannot_advance(self):
        self.client.force_authenticate(self.noble)
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_advance(self):
        res = self.client.post(self.url())
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
