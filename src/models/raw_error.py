class SearchIndexNotReady(Exception):
    def __init__(self, message: str, retry_after: float, documents_indexed: int):
        self.message = message
        self.retry_after = retry_after
        self.documents_indexed = documents_indexed
        super().__init__(f"{message} (Retry after: {retry_after}s)")

class SearchAPIError(Exception):
    def __init__(self, status: int, response_text: str):
        self.status = status
        self.response_text = response_text
        super().__init__(f"Discord API Error {status}: {response_text}")