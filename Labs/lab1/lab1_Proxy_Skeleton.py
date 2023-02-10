# 50.012 network lab 1
# Adapted from K & R's original code

from socket import *
import sys
import thread
import os


proxy_port = 8079
cache_directory = "./"


def client_thread(tcpCliSock):

    tcpCliSock.settimeout(5.0)

    try:
        message = tcpCliSock.  # Fill in start                      # Fill in end
    except:
        print("error", str(sys.exc_info()[0]))
        tcpCliSock.close()
        return

    print(message)

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

    file_to_use = cache_directory + resource.replace("/", ".")

    fileExist = False

    try:
        # Check wether the file exist in the cache
        f = open(file_to_use, "r")

        print('Serve from cache')
        outputdata = f.readlines()
        fileExist = True
        # ProxyServer finds a cache hit and generates a response message

        # Fill in start

        # Fill in end

    # Error handling for file not found in cache
    except IOError:
        if fileExist == False:
            # Create a socket on the proxyserver
            c =  # Fill in start              # Fill in end
            try:
                cacheFile = open(file_to_use, "wb")

                # Connect to the webServer and request for its client

                # Fill in start

                # Fill in end

                while 1:
                    buff = c.recv(2048)
                    cacheFile.write(buff)
                    if len(buff) > 0:
                        tcpCliSock.send(buff)
                    else:
                        break

            except gaierror as e:
                print("error", e)

            except:
                print("Illegal request", str(sys.exc_info()[0]))
            finally:

                # Fill in start

                # Fill in end
                cacheFile.close()

        else:
            # HTTP response message for file not found
            # Fill in start

            # Fill in end

    finally:
        # Close the socket after use
        # Fill in start

        # Fill in end

        f.close()


if len(sys.argv) <= 1:
    print(
        'Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)

# Fill in start


# Fill in end

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

    # Fill in end
