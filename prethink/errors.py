class PrethinkError(Exception):
    """Base class for all marshmallow-related errors."""


class ValidationError(PrethinkError):
    def __init__(
        self,
        message,
        field_name='_schema',
        data=None,
        valid_data=None,
        **kwargs
    ):
        if isinstance(message, (str, bytes)):
            self.messages = [message]
        else:
            self.messages = message
        self.field_name = field_name
        self.data = data
        self.valid_data = valid_data
        self.kwargs = kwargs
        super().__init__(message)

    def normalized_messages(self):
        if self.field_name == '_schema' and isinstance(self.messages, dict):
            return self.messages
        return {self.field_name: self.messages}
