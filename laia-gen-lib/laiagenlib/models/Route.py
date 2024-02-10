class Route:
    def __init__(self, path, method, summary, responses, extensions):
        self.path = path
        self.method = method
        self.summary = summary
        self.responses = responses
        self.extensions = extensions

    def __str__(self):
        return f"Path: {self.path}, Method: {self.method}, Summary: {self.summary}, Responses: {self.responses}, Extensions: {self.extensions}"
