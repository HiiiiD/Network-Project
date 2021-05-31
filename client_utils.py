from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from typing import Callable


def create_socket_thread(address: tuple[str, int], thread_func: Callable):
    """Create a socket that connects to the specified `address` and starts a thread with the `thread_func`

    Parameters
    ----------
    address : tuple[str, int]
        address used for connecting the socket
    thread_func : Callable
        function that is working on the thread
    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    sock_thread = Thread(target=thread_func)
    sock_thread.setDaemon(True)
    sock_thread.start()
    return sock, sock_thread
