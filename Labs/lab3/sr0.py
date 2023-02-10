"""
Bugs:
- can't find some elements in window_timer dict. It could be possible that the timer has
not been cancelled cleanly, hence triggering timeout although its been removed 
from window_timer QUICKFIX applied: if condition statement
- duplicate packets to receiver are dealt with
- duplicate ACKs (after receiving them already) are dealt with

- Timer for packet behind window is still triggering timeout
--- sender_base should only shift when lowest sequence number has been sent

- ACKs sent by receiver takes very long before being received by sender
"""


import config
import threading
import time
import udt
import util


# Go-Back-N reliable transport protocol.
class SelectiveRepeat:

    NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

    # "msg_handler" is used to deliver messages to application layer
    def __init__(self, local_port, remote_port, msg_handler):
        """
        set_timer removed as there're multiple timers, and we'll set them right after its
          respective packet has been sent

        self.window_timer - dictionary of timers for each packet. will be removed once ACK received
        self.receiver_buffer - unordered packets are kept here, and whenever they're sent up to application, they'll be removed
        """
        util.log("Starting up `Selective Repeat` protocol ... ")
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.sender_base = 0
        self.next_sequence_number = 0
        self.window = [b'']*config.WINDOW_SIZE
        self.expected_sequence_number = 0
        self.receiver_last_ack = b''
        self.is_receiver = True
        self.sender_lock = threading.Lock()

        self.window_timer = {}
        self.receiver_buffer = {}
        self.sender_buffer = []

    # def set_timer(self):
        # self.timer = threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout)

    def set_timer(self, seq_num):
        return threading.Timer(config.TIMEOUT_MSEC/1000.0, self._timeout, args=[seq_num])

    # "send" is called by application. Return true on success, false otherwise.

    def send(self, msg):
        """
        gbn:
        Checks if packet is within send window before sending
        """
        self.is_receiver = False
        if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):
            self._send_helper(msg)
            return True
        else:
            util.log("Window is full. App data rejected.")
            time.sleep(1)
            return False

    # Helper fn for thread to send the next packet

    def _send_helper(self, msg):
        """
        gnb:
        1. Make packet
        2. Allocate packet to a slot in the window
        3. Send packet
        4. If its first packet, set timer for packet
        5. Increase sequence number

        sr:
        1. Make packet
        2. Allocate packet to a slot in the window
        3. Send packet
        4. set and start timer for packet in a dict
        5. Increase sequence number
        """

        self.sender_lock.acquire()
        packet = util.make_packet(
            msg, config.MSG_TYPE_DATA, self.next_sequence_number)
        packet_data = util.extract_data(packet)

        self.window[self.next_sequence_number % config.WINDOW_SIZE] = packet

        util.log("Sending data: " + util.pkt_to_string(packet_data))
        self.network_layer.send(packet)

        self.window_timer[self.next_sequence_number] = self.set_timer(
            self.next_sequence_number)
        self.window_timer[self.next_sequence_number].start()

        self.next_sequence_number += 1
        self.sender_lock.release()
        return

    # "handler" to be called by network layer when packet is ready.

    def handle_arrival_msg(self):
        """
        gbn:
        1. Receives message
        2. If message is corrupted, resend ACK
        3. If message is ACK, we're sender
          a. increase sender window base by 1
          b. assuming next_sequence_number increases faster than sender_base, 
            timer is cancelled once last packet has been sent. otherwise just restart
            the timer
        4. If message is data, we're receiver
          a. If msg_data.seq_num == self.expected_sequence_number
            1. send msg content to msg_handler
            2. create and send ACK packet
            3. set ACK packet as receiver_last_ack
            4. increase expected_sequence_number by 1
          b. else
            1. if expected_sequence_number != 0, resend receiver_last_ack

        sr:
        1. Receives message
        2. If message is corrupted, resend ACK
        3. If message is ACK, we're sender
          a. if ACK is within sender window
            1. cancel timer and delete key:value for that sequence number
            2. add msg_data.seq_num into sender_buffer
            3. while window_base is in sender_buffer:
              a. del window_base from sender_buffer
              b. window_base += 1
          b. else if ACK is behind sender window
            1. Remove timer if exists
          c. else ignore
        4. If message is data, we're receiver
          a. if packet is within receiver window
            1. Add message into receiver_buffer dict using msg_data.seq_num as key
            2. update receiver_last_ack in case next message is corrupted
            3. while self.expected_sequence_number is in receiver_buffer
              a. send msg content to msg_handler
              b. create and send ACK packet
              c. Delete receiver_buffer[self.expected_sequence_number] key:value pair
              d. increase expected_sequence_number by 1
          b. else if window has already shifted beyond packet
            1. send ACK
          c. else if window has not shifted to packet
            1. Ignore
        """

        msg = self.network_layer.recv()
        msg_data = util.extract_data(msg)

        if(msg_data.is_corrupt):
            if(self.is_receiver):
                if self.expected_sequence_number == 0:
                    util.log("Packet received is corrupted. " +
                             self.NO_PREV_ACK_MSG)
                    return
                self.network_layer.send(self.receiver_last_ack)
                util.log("Received corrupted data. Resending ACK: "
                         + util.pkt_to_string(util.extract_data(self.receiver_last_ack)))
            return

        # If ACK message, assume its for sender
        if msg_data.msg_type == config.MSG_TYPE_ACK:
            self.sender_lock.acquire()
            print(
                "handle_arrival_msg (sender): - msg_data.seq_num: {0}".format(msg_data.seq_num))
            print("handle_arrival_msg (sender): - sender_base: {0}; sender_buffer: {1}".format(
                self.sender_base, self.sender_buffer))
            print(
                "handle_arrival_msg (sender): - self.window_timer: {0}".format(self.window_timer))

            # a. if ACK is within sender window
            if self.sender_base <= msg_data.seq_num and self.sender_base+config.WINDOW_SIZE > msg_data.seq_num:
                # 1. cancel timer and delete key:value for that sequence number if it exist
                if msg_data.seq_num in self.window_timer.keys():
                    self.window_timer[msg_data.seq_num].cancel()
                    del self.window_timer[msg_data.seq_num]
                    # print("handle_arrival_msg: --- self.window_timer.keys(): {0}".format(self.window_timer.keys))

                # 2. add msg_data.seq_num into sender_buffer
                self.sender_buffer.append(msg_data.seq_num)

                # 3. while window_base is in sender_buffer:
                while self.sender_base in self.sender_buffer:
                    # a. del window_base from sender_buffer
                    self.sender_buffer.remove(self.sender_base)

                    ### b. window_base += 1
                    self.sender_base += 1

            # b. else ignore
            elif self.sender_base > msg_data.seq_num:
                print(
                    "handle_arrival_msg: --- self.sender_base > msg_data.seq_num; msg_data.seq_num: {0}".format(msg_data.seq_num))
            elif self.sender_base+config.WINDOW_SIZE <= msg_data.seq_num:
                print("handle_arrival_msg: --- self.sender_base <= msg_data.seq_num")
            else:
                print("uncaught condition in ACK receiver")

            self.sender_lock.release()
        # If DATA message, assume its for receiver
        else:
            assert msg_data.msg_type == config.MSG_TYPE_DATA
            util.log("Received DATA: " + util.pkt_to_string(msg_data))
            print("handle_arrival_msg (receiver): - self.expected_sequence_number: {0}".format(
                self.expected_sequence_number))
            print(
                "handle_arrival_msg (receiver): - msg_data.seq_num: {0}".format(msg_data.seq_num))
            print(
                "handle_arrival_msg (receiver): - receive_buffer: {0}".format(self.receiver_buffer))

            # a. if packet is within receiver window
            if self.expected_sequence_number <= msg_data.seq_num and self.expected_sequence_number+config.WINDOW_SIZE > msg_data.seq_num:
                # 1. Add message into receiver_buffer dict using msg_data.seq_num as key
                self.receiver_buffer[msg_data.seq_num] = msg_data.payload
                print()

                # 2. update receiver_last_ack in case next message is corrupted
                self.receiver_last_ack = util.make_packet(
                    b'', config.MSG_TYPE_ACK, msg_data.seq_num)

                # 3. while self.expected_sequence_number is in receiver_buffer
                while self.expected_sequence_number in self.receiver_buffer:
                    # a. send msg content to msg_handler
                    self.msg_handler(
                        self.receiver_buffer[self.expected_sequence_number])

                    # b. create and send ACK packet
                    ack_pkt = util.make_packet(
                        b'', config.MSG_TYPE_ACK, self.expected_sequence_number)
                    self.network_layer.send(ack_pkt)

                    # c. Delete self.receiver_buffer[self.expected_sequence_number] key:value pair
                    del self.receiver_buffer[self.expected_sequence_number]

                    # d. increase expected_sequence_number by 1
                    self.expected_sequence_number += 1
                    util.log("Sent ACK: " +
                             util.pkt_to_string(util.extract_data(ack_pkt)))

            # b. else if window has already shifted beyond packet
            elif self.expected_sequence_number > msg_data.seq_num:
                # 1. send ACK
                ack_pkt = util.make_packet(
                    b'', config.MSG_TYPE_ACK, msg_data.seq_num)
                self.network_layer.send(ack_pkt)
                util.log("Sent ACK: " +
                         util.pkt_to_string(util.extract_data(ack_pkt)))

            # c. else if window has not shifted to packet
            elif self.expected_sequence_number+config.WINDOW_SIZE <= msg_data.seq_num:
                # 1. Ignore
                pass

        return

    # Cleanup resources.

    def shutdown(self):
        if not self.is_receiver:
            self._wait_for_last_ACK()
        for timers in self.window_timer.keys():
            if self.window_timer[timers].is_alive():
                self.window_timer[timers].cancel()
        util.log("Connection shutting down...")
        self.network_layer.shutdown()

    def _wait_for_last_ACK(self):
        while self.sender_base < self.next_sequence_number-1:
            util.log("Waiting for last ACK from receiver with sequence # "
                     + str(int(self.next_sequence_number-1)) + ".")
            time.sleep(1)

    def _timeout(self, seq_num):
        """
        gbn:
        1. Reset timer
        2. From start of window to end of window, resend all packets
        3. Start timer

        sr:
        1. Reset timer
        2. Resend packet with seq_num
        3. Start timer
        """
        self.sender_lock.acquire()
        util.log("Timeout! Resending packet with seq # " + str(seq_num) + ".")

        # the if condition is a quick fix as i suspect timeout might still be called when
        # the timer has been deleted from window_timer due to concurrency issues
        if seq_num in self.window_timer.keys():
            # 1. Reset timer
            if self.window_timer[seq_num].is_alive():
                self.window_timer[seq_num].cancel()
            self.window_timer[seq_num] = self.set_timer(seq_num)

            # 2. Resend packet with seq_num
            pkt = self.window[seq_num % config.WINDOW_SIZE]
            self.network_layer.send(pkt)
            util.log("Resending packet: " +
                     util.pkt_to_string(util.extract_data(pkt)))

            # 3. Start timer
            self.window_timer[seq_num].start()

        self.sender_lock.release()
        return
