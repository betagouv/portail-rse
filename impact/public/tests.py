from django.test import TestCase


class IndexTest(TestCase):
    def test(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<!-- page index -->")
