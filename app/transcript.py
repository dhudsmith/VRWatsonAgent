
class Transcript:
    """
    This class encapsulates the current transaction with the original message
    and assistant response
    """
    def __init__(self, original, response):
        self.assistantResponse = response
        self.originalMessage = original
