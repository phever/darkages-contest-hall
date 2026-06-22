from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Contest, Entry, Invitation, User


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


class EntryEditTests(APITestCase):
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

    def url(self):
        return f'/api/entries/{self.entry.id}/'

    def test_chancellor_can_edit_all_fields(self):
        self.client.force_authenticate(self.chancellor)
        res = self.client.patch(self.url(), {
            'work_title': 'On the Library of Loures',
            'review_overseer': 'Laurier',
            'recommendation': 'Kingdom',
            'current_step': 3,
            'step_status': 'Loures Confirmation',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.work_title, 'On the Library of Loures')
        self.assertEqual(self.entry.review_overseer, 'Laurier')
        self.assertEqual(self.entry.recommendation, 'Kingdom')
        self.assertEqual(self.entry.current_step, 3)
        self.assertEqual(res.data['on_step'], '3/4 - Loures Confirmation')

    def test_noble_cannot_edit(self):
        self.client.force_authenticate(self.noble)
        res = self.client.patch(self.url(), {'work_title': 'Hijacked'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_edit(self):
        res = self.client.patch(self.url(), {'work_title': 'Hijacked'}, format='json')
        self.assertIn(res.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class ArchiveTests(APITestCase):
    def setUp(self):
        self.contest = Contest.objects.create(title='Mileth College Contest Hall')
        self.chancellor = User.objects.create_user(
            username='chancellor', password='x', role='admin', is_staff=True,
        )
        # Two live board entries...
        Entry.objects.create(contest=self.contest, entrant_name='Aengus',
                             work_title='On Loures', work_subject='Lore')
        Entry.objects.create(contest=self.contest, entrant_name='Brigid',
                             work_title='Sunhymn', work_subject='Persona')
        # ...and two archived works.
        Entry.objects.create(contest=self.contest, entrant_name='Cael',
                             work_title='Ancient Ballad', work_subject='Persona',
                             is_archived=True)
        Entry.objects.create(contest=self.contest, entrant_name='Deirdre',
                             work_title='Old Tapestry', work_subject='Art',
                             is_archived=True)

    def test_default_list_excludes_archived(self):
        res = self.client.get('/api/entries/')
        titles = {e['work_title'] for e in res.data}
        self.assertEqual(titles, {'On Loures', 'Sunhymn'})

    def test_archived_filter_returns_only_archived(self):
        res = self.client.get('/api/entries/?archived=true')
        titles = {e['work_title'] for e in res.data}
        self.assertEqual(titles, {'Ancient Ballad', 'Old Tapestry'})

    def test_archive_search_by_title(self):
        res = self.client.get('/api/entries/?archived=true&search=tapestry')
        self.assertEqual([e['work_title'] for e in res.data], ['Old Tapestry'])

    def test_archive_search_by_entrant(self):
        res = self.client.get('/api/entries/?archived=true&search=Cael')
        self.assertEqual([e['work_title'] for e in res.data], ['Ancient Ballad'])

    def test_archive_filter_by_category(self):
        res = self.client.get('/api/entries/?archived=true&subject=Persona')
        self.assertEqual([e['work_title'] for e in res.data], ['Ancient Ballad'])

    def test_board_contest_excludes_archived(self):
        res = self.client.get(f'/api/contests/{self.contest.id}/')
        titles = {e['work_title'] for e in res.data['entries']}
        self.assertEqual(titles, {'On Loures', 'Sunhymn'})
        self.assertEqual(res.data['entry_count'], 2)

    def test_chancellor_creates_archived_work(self):
        self.client.force_authenticate(self.chancellor)
        res = self.client.post('/api/entries/', {
            'contest': self.contest.id, 'entrant_name': 'Eira',
            'work_title': 'Lost Scroll', 'work_subject': 'Literature',
            'is_archived': True,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_archived'])
        self.assertEqual(res.data['step_status'], 'Archived')

    def test_noble_cannot_create_archived_work(self):
        noble = User.objects.create_user(username='n', password='x', role='voter')
        self.client.force_authenticate(noble)
        res = self.client.post('/api/entries/', {
            'contest': self.contest.id, 'entrant_name': 'X', 'work_title': 'Y',
            'is_archived': True,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class InvitationTests(APITestCase):
    def setUp(self):
        self.chancellor = User.objects.create_user(
            username='chancellor', password='x', role='admin', is_staff=True,
        )
        self.noble = User.objects.create_user(
            username='noble', password='x', role='voter', is_verified=True,
        )

    def test_chancellor_creates_invitation_and_email_sent(self):
        self.client.force_authenticate(self.chancellor)
        res = self.client.post('/api/invitations/', {
            'email': 'NewNoble@example.com', 'in_game_name': 'Sundeep',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('token', res.data)  # token must never be exposed by the API
        self.assertEqual(res.data['status'], 'pending')
        invitation = Invitation.objects.get(email='newnoble@example.com')
        self.assertEqual(invitation.invited_by, self.chancellor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(invitation.token, mail.outbox[0].body)

    def test_noble_cannot_invite(self):
        self.client.force_authenticate(self.noble)
        res = self.client.post('/api/invitations/', {'email': 'x@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_invite_existing_email(self):
        self.client.force_authenticate(self.chancellor)
        self.noble.email = 'taken@example.com'
        self.noble.save()
        res = self.client.post('/api/invitations/', {'email': 'taken@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invitation_creates_verified_voter(self):
        invitation = Invitation.objects.create(
            email='newnoble@example.com', in_game_name='Sundeep',
            token=Invitation.generate_token(),
        )
        # Detail lookup prefills email + in-game name (read-only for the noble).
        detail = self.client.get(f'/api/auth/invitation/?token={invitation.token}')
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data['in_game_name'], 'Sundeep')

        res = self.client.post('/api/auth/accept-invite/', {
            'token': invitation.token, 'username': 'sundeep', 'password': 'corrhorse42xy',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='sundeep')
        self.assertEqual(user.email, 'newnoble@example.com')
        self.assertEqual(user.in_game_name, 'Sundeep')
        self.assertEqual(user.role, 'voter')
        self.assertTrue(user.is_verified)
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.accepted_at)

    def test_invitation_token_is_single_use(self):
        invitation = Invitation.objects.create(
            email='once@example.com', token=Invitation.generate_token(),
        )
        payload = {'token': invitation.token, 'username': 'oncey', 'password': 'corrhorse42xy'}
        first = self.client.post('/api/auth/accept-invite/', payload, format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        second = self.client.post('/api/auth/accept-invite/',
                                  {**payload, 'username': 'oncey2'}, format='json')
        self.assertEqual(second.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_rejects_weak_password(self):
        invitation = Invitation.objects.create(
            email='weak@example.com', token=Invitation.generate_token(),
        )
        res = self.client.post('/api/auth/accept-invite/', {
            'token': invitation.token, 'username': 'weakling', 'password': '123',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='weakling').exists())
