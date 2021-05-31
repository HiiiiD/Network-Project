from typing import List
from socket import socket


def read_message(sock: socket, buf_size: int = 1024) -> List[str]:
    """Read a message from the server, then return a list of messages sent by the server

    Parameters
    ----------
    sock : socket
        socket used to read the message
    buf_size : int
        size of the buffer(in bytes) used by the socket to read the message (default is 1024)

    Returns
    -------
    list[str]
        a list of messages split by the sequence '\\r\\n\\r\\n'
    """
    message = sock.recv(buf_size).decode("utf8")
    return list(filter(None, message.split('\r\n\r\n')))
