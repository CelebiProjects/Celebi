"""
Created by Mingrui Zhao @ 2025
define the messages class
"""

from typing import List, Tuple
from .pretty import colorize

class Message:
    """ A class to define messages used in the project,
    the message is a list with tuple (text, type), for different typing purpose
    """

    def __init__(self) -> None:
        self.messages: List[Tuple[str, str]] = []

    def __str__(self) -> str:
        """ String representation of the messages
        """
        return "".join(f"{msg_type}: {text}" for text, msg_type in self.messages)

    def add(self, text: str, msg_type: str = "") -> None:
        """ Add a message to the list
        """
        self.messages.append((text, msg_type))

    def append(self, other: 'Message') -> None:
        """ Append another Message object to this one
        """
        if isinstance(other, Message):
            self.messages.extend(other.messages)
        else:
            raise TypeError("Expected a Message instance")

    def colored(self) -> str:
        """ Return colored messages
        """
        return "".join(colorize(text, msg_type) for text, msg_type in self.messages)
