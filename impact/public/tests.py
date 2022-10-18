from django.test import Client


# class IndexTest(TestCase):
#     def test(self):
#         response = self.client.get("/")

#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "<!-- page index -->")

def test_index():
    response = Client().get("/")

    assert response.status_code == 200
    assert "<!-- page index -->" in str(response.content)
