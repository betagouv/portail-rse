class MockedResponse:
    def __init__(self, status_code, json_content=""):
        self.status_code = status_code
        self.json_content = json_content

    def json(self):
        return self.json_content
