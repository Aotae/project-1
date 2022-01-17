"""
  A trivial web server in Python.

  Based largely on https://docs.python.org/3.4/howto/sockets.html
  This trivial implementation is not robust:  We have omitted decent
  error handling and many other things to keep the illustration as simple
  as possible.

  FIXME:
  Currently this program always serves an ascii graphic of a cat.
  Change it to serve files if they end with .html or .css, and are
  located in ./pages  (where '.' is the directory from which this
  program is run).

  Used OS and __file__ to find current working directory and where pageserver.py is running from
  assumming that pageserver.py and config.py never leaves the pageserver folder in the repo this should work.
"""

import config    # Configure from .ini files and command line
import logging   # Better than print statements
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
# Logging level may be overridden by configuration 

import socket    # Basic TCP/IP communication on the internet
import _thread   # Response computation runs concurrently with main program
import os



def listen(portnum):
    """
    Create and listen to a server socket.
    Args:
       portnum: Integer in range 1024-65535; temporary use ports
           should be in range 49152-65535.
    Returns:
       A server socket, unless connection fails (e.g., because
       the port is already in use).
    """
    # Internet, streaming socket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to port and make accessible from anywhere that has our IP address
    serversocket.bind(('', portnum))
    serversocket.listen(1)    # A real server would have multiple listeners
    return serversocket


def serve(sock, func, docroot):
    """
    Respond to connections on sock.
    Args:
       sock:  A server socket, already listening on some port.
       func:  a function that takes a client socket and does something with it
    Returns: nothing
    Effects:
        For each connection, func is called on a client socket connected
        to the connected client, running concurrently in its own thread.
    """
    while True:
        log.info("Attempting to accept a connection on {}".format(sock))
        (clientsocket, address) = sock.accept()
        _thread.start_new_thread(func, (clientsocket, docroot))
##
# Starter version only serves cat pictures. In fact, only a
# particular cat picture.  This one.
##
CAT = """
     ^ ^
   =(   )=
"""

# HTTP response codes, as the strings we will actually send.
# See:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
# or    http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
##
STATUS_OK = "HTTP/1.0 200 OK\n\n"
STATUS_FORBIDDEN = "HTTP/1.0 403 Forbidden\n\n"
STATUS_NOT_FOUND = "HTTP/1.0 404 Not Found\n\n"
STATUS_NOT_IMPLEMENTED = "HTTP/1.0 401 Not Implemented\n\n"


def respond(sock, docroot):
    """
    This server responds only to GET requests (not PUT, POST, or UPDATE).
    Any valid GET request is answered with an ascii graphic of a cat.
    """
    file_exists = False
    sent = 0
    request = sock.recv(1024)  # We accept only short requests
    request = str(request, encoding='utf-8', errors='strict')
    log.info("--- Received request ----")
    log.info("Request was {}\n***\n".format(request))
    # Kind of a jank way to get the directory
    # get the parent of the directory running pageserver.py
    # this should always be the pageserver folder
    # so we can actually chdir 
    parts = request.split()

    log.info((os.path.dirname(os.path.abspath(config.__file__))))
    log.info(os.path.abspath(config.__file__))
    os.chdir(os.path.dirname(os.path.abspath(config.__file__)))
    a = os.getcwd()
    log.info(a)
    log.info(parts)
    parent = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    log.info(parent)
    os.chdir(parent+os.sep+docroot)
    log.info(os.getcwd())
    pages_list = os.listdir()
    log.info(pages_list)
    if len(parts) > 1 and parts[0] == "GET":
        file_name = parts[1]
        # will stop at first page that matches the request
        # all pages in pages should be unique
        if file_name == '/':
            transmit(STATUS_OK,sock)
            transmit(CAT,sock)
            os.chdir(a)
        else:
            if ".." in file_name or "~" in file_name:
                transmit(STATUS_FORBIDDEN,sock)
                transmit("403 Forbidden, special characters .. and ~ not allowed", sock)
            else:
                file_exists = os.path.exists(file_name[1:])
                if file_exists:
                    transmit(STATUS_OK, sock)
                    f = open(file_name[1:], 'r')
                    file = f.read()
                    f.close()
                    transmit(file,sock)
                    log.info(a)
                    os.chdir(a)
                else:
                    transmit(STATUS_NOT_FOUND, sock)
                    transmit("404 Not Found, Page not found",sock)
                    os.chdir(a)


    else:
        log.info("Unhandled request: {}".format(request))
        transmit(STATUS_NOT_IMPLEMENTED, sock)
        transmit("\nI don't handle this request: {}\n".format(request), sock)

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    return

def transmit(msg, sock):
    """It might take several sends to get the whole message out"""
    sent = 0
    while sent < len(msg):
        buff = bytes(msg[sent:], encoding="utf-8")
        sent += sock.send(buff)

###
#
# Run from command line
#
###

def get_options():
    """
    Options from command line or configuration file.
    Returns namespace object with option value for port
    """
    # Defaults from configuration files;
    #   on conflict, the last value read has precedence
    options = config.configuration()
    # We want: PORT, DOCROOT, possibly LOGGING

    if options.PORT <= 1000:
        log.warning(("Port {} selected. " +
                         " Ports 0..1000 are reserved \n" +
                         "by the operating system").format(options.port))

    return options

def main():
    options = get_options()
    port = options.PORT
    docroot = options.DOCROOT
    log.info(os.getcwd())
    if options.DEBUG:
        log.setLevel(logging.DEBUG)
    sock = listen(port)
    log.info("Listening on port {}".format(port))
    log.info("Socket is {}".format(sock))
    serve(sock, respond, docroot)

if __name__ == "__main__":
    main()
