# 50.012 network lab 1
# Adapted from K & R's original code

from socket import *
import sys
import _thread as thread
import os
from functools import lru_cache


proxy_port = 8079
cache_directory = "./"

# Acts as a caching mechanism without saving the page.
@lru_cache(maxsize=512)
def proxy_cache(webServer, resource, port, message):
    "retrieve resource if not cached; else return cached."
    proxySock = socket(AF_INET, SOCK_STREAM)
    proxySock.connect((webServer, port))
    print("Socket GET", end="..")

    proxySock.sendall(bytes(message, encoding='ascii'))

    chunks = []
    print("receiving.", end="")
    while True:
        print(".", end="")
        buffer = proxySock.recv(1024)
        if len(buffer) > 0:
            chunks.append(buffer)
            print(".", end="")
        else:
            break

    proxySock.close()
    fullChunk = b''.join(chunks)
    print(len(fullChunk), end="..")
    return fullChunk


def client_thread(tcpCliSock):

    tcpCliSock.settimeout(5.0)

    try:
        message = tcpCliSock.recv(4096).decode("ascii")
    except:
        print("error", str(sys.exc_info()[0]))
        tcpCliSock.close()
        return

    # print(message)

    # Extract the following info from the received message
    #   webServer: the web server's host name
    #   resource: the web resource requested
    #   file_to_use: a valid file name to cache the requested resource
    #   Assume the HTTP reques is in the format of:
    #      GET http://www.ucla.edu/img/apple-touch-icon.png HTTP/1.1\r\n
    #      Host: www.ucla.edu\r\n
    #      User-Agent: .....
    #      Accept:  ......

    msgElements = message.split()

    if len(msgElements) < 5:
        print("non-supported request: ", msgElements)
        tcpCliSock.close()
        return

    if msgElements[0].upper() != 'GET' or msgElements[3].upper() != 'HOST:':
        print("non-supported request", msgElements[0], msgElements[3])
        tcpCliSock.close()
        return

    resource = msgElements[1].replace("http://", "", 1)

    webServer = msgElements[4]

    port = 80

    print("webServer:", webServer)
    print("resource:", resource)

    message = message.replace("Connection: keep-alive", "Connection: close")

    if ":443" in resource:
        port = 443
        print("Sorry, so far our program cannot deal with HTTPS yet")
        tcpCliSock.close()
        return

    print("Requesting...", end="")
    resourceReqested = proxy_cache(webServer, resource, port, message)
    print("acquired.")
    tcpCliSock.send(resourceReqested)

    tcpCliSock.close()

if len(sys.argv) <= 1:
    print(
        'Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.bind((sys.argv[1], proxy_port))
tcpSerSock.listen(15)

print('Proxy ready to serve at', sys.argv[1], proxy_port)

try:
    while True:
        # Start receiving data from the client
        tcpCliSock, addr = tcpSerSock.accept()
        print('Received a connection from:', addr)

        # the following function starts a new thread, taking the function name as the first argument, and a tuple of arguments to the function as its second argument
        thread.start_new_thread(client_thread, (tcpCliSock, ))

except KeyboardInterrupt:
    print('bye...')

finally:
    # Close the socket after use
    # Fill in start
    tcpSerSock.close()
    # Fill in end
