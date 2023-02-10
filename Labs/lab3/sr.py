import config
import threading
import time
import udt
import util

"""
Done by Lee Gui An (1002651) - github.com/piroton
"""

# Selective Repeat Procotol


class SelectiveRepeat:

    NO_PREV_ACK_MSG = "No ACK to send, waiting for timeout."

    # "msg_handler" is used to deliver messages to application layer
    def __init__(self, local_port, remote_port, msg_handler):
        util.log("Starting 'Selective Repeat' protocol ...")
        util.log("Setting up Network Layers...")
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.is_receiver = True

        util.log("Initializing Packet Windows...")
        self.sequence_number = 0
        self.seq_send_next = 0
        self.exp_rcv_next = 0
        self.send_lock = threading.Lock()
        self.msg_window = [b'']*config.WINDOW_SIZE
        self.receiver_last_ack = b''

        util.log("Allocating space for send/receive windows...")
        self.timers = {}
        self.rcv_buf = {}
        self.acked_pkts = []

        util.log("Protocol Ready.")
        # self.last_pkt_sent = b''
        # self.last_pkt_sent_data = None
        # self.sender_lock = threading.Lock()
        # self.sender_state = config.WAIT_FOR_APP_DATA
        # self.set_timer()
        # self.is_receiver = True
        # self.sliding_window = Queue(maxsize=8)
        # self.requests = Queue()

    def set_timer(self, slot_num):
        """Sets up a timer for a given sequence number.

        input: seq_num: integer number of sent sequence.
        """
        return threading.Timer(
            (config.TIMEOUT_MSEC/1000.0), self._timeout, args=[slot_num])

    # "send" is called by application. Return true on success, false otherwise.
    def send(self, msg):
        self.is_receiver = False
        # Check if the next sequence number is within the send window:
        window_limit = (self.sequence_number + config.WINDOW_SIZE)
        if self.seq_send_next < window_limit:
            self._send_helper(msg)
            return True
        else:
            util.log("Window is full, rejecting App Data.")
            time.sleep(1)
            return False

    # Helper fn for thread to send the next packet
    def _send_helper(self, msg):
        """
        Generates a data packet which is checked into the send window,
        and then sent to the receiver, starting an individual timer..
        """
        # Make Packet
        self.send_lock.acquire()
        packet = util.make_packet(
            msg, config.MSG_TYPE_DATA, self.seq_send_next)
        packet_data = util.extract_data(packet)
        util.log("Sending Packet {}".format(self.seq_send_next))

        # Allocate Slot
        rolling_seq = self.seq_send_next % config.WINDOW_SIZE
        self.msg_window[rolling_seq] = packet

        # Set Timer for packet
        next_num = self.seq_send_next
        self.timers[next_num] = self.set_timer(next_num)

        # Send Packet, start timer
        util.log("Sending data: " + util.pkt_to_string(packet_data))
        self.network_layer.send(packet)
        self.timers[next_num].start()

        # Increment Seqnum
        self.seq_send_next += 1
        self.send_lock.release()
        return

    def handle_receiver(self, msg_data):
        """Handles data incoming as a receiver."""
        """
        check seqnum;
        if not in window or less: ignore
        send ACK(seqnum)
        if seqnum in window:
            add to rcv_buffer
            while exp_next in rcv_buffer:
                push(rcv_buffer[exp_next])
                increment exp_next

        """
        if msg_data.msg_type == config.MSG_TYPE_DATA:
            rcv_num = msg_data.seq_num
            util.log("Received Data Num: {}".format(rcv_num))
            util.log("Data: {}".format(util.pkt_to_string(msg_data)))

            # Check for rcv_num in window ceiling
            window_max = self.exp_rcv_next + config.WINDOW_SIZE
            exp_next = self.exp_rcv_next

            # if rcv < exp_next: resend ACK
            if rcv_num <= (exp_next):
                ack_pkt = util.make_packet(
                    b'', config.MSG_TYPE_ACK, exp_next)
                self.network_layer.send(ack_pkt)
                util.log("Sent ACK: {}".format(rcv_num))

            # if rcv in window: send ACK, add to buffer
            elif rcv_num < window_max:
                self.rcv_buf[rcv_num] = msg_data.payload
                ack_pkt = util.make_packet(
                    b'', config.MSG_TYPE_ACK, exp_next)
                self.receiver_last_ack = ack_pkt
                self.network_layer.send(ack_pkt)
                util.log("Sent ACK: {}".format(rcv_num))

                # output chunks in order, increment exp_next
                while self.exp_rcv_next in self.rcv_buf:
                    self.msg_handler(self.rcv_buf[exp_next])
                    del self.rcv_buf[exp_next]
                    self.exp_rcv_next += 1
            # else ignore
            else:
                pass

        else:
            util.log("Error: Attempting to send ACK to receiver.")

        return

    def handle_sender(self, msg_data):
        """Handles data incoming as a sender."""
        """ Check Seqnum
        Add seqnum to acked_pkts
        while send_base in acked_pkts:
            delete send_base, increment
        if ACK not in send_window:
            IGNORE
        """
        if msg_data.msg_type == config.MSG_TYPE_ACK:
            util.log("Received Packet no: {}".format(msg_data.seq_num))
            # Pause Sending
            self.send_lock.acquire()
            # Check SEQ NUM
            rcv_num = msg_data.seq_num
            base = self.sequence_number
            window_max = base + config.WINDOW_SIZE
            util.log("Current Window: {} - {}".format(base, window_max))

            # Check that ACK is in window:
            ACK_window = range(base, window_max+1)
            if rcv_num in ACK_window:
                # Stop the timer for the packet
                if rcv_num in self.timers.keys():
                    self.timers[rcv_num].cancel()
                    del self.timers[rcv_num]

                # Add to the ACKed list
                self.acked_pkts.append(rcv_num)

                # Remove all packets already ACKed from smallest up
                while self.sequence_number in self.acked_pkts:
                    self.acked_pkts.remove(self.sequence_number)
                    self.sequence_number += 1
            # Ignore packets not in ACK window.
            else:
                util.log("Received Packet {} not in Window[{}:{}], dumping.".format(
                    rcv_num, base, window_max))
        else:
            util.log("Error: Sender received non-ACK packet.")
        self.send_lock.release()
        return

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        """
        Handles reception of inbound message packet.
        """
        # Receive Message, Extract Data
        msg = self.network_layer.recv()
        msg_data = util.extract_data(msg)

        # Check for corrupted packets

        if(msg_data.is_corrupt):
            if(self.is_receiver):
                if self.exp_rcv_next == 0:
                    util.log("Packet received is corrupted. " +
                             self.NO_PREV_ACK_MSG)
                    return
                self.network_layer.send(self.receiver_last_ack)
                util.log("Received corrupted data. Resending ACK: " +
                         util.pkt_to_string(
                             util.extract_data(self.receiver_last_ack)))

        if self.is_receiver:
            self.handle_receiver(msg_data)
        else:
            self.handle_sender(msg_data)
        return

    # Cleanup resources.
    def shutdown(self):
        if not self.is_receiver:
            self._wait_for_last_ACK()
        for timer in self.timers.values():
            if timer.is_alive():
                timer.cancel()
        util.log("Connection shutting down...")
        self.network_layer.shutdown()

    def _wait_for_last_ACK(self):
        while self.sequence_number < self.seq_send_next-1:
            util.log("Waiting for last ACK from receiver with sequence # "
                     + str(int(self.seq_send_next-1)) + ".")
            time.sleep(1)

    def _timeout(self, seq_num):
        """
        Timeout: Resend specific packet with seq_num (because failed to return on time)
        Reset Timer > Resend Packet > Start Timer
        """
        # Acquire Sending Lock
        self.send_lock.acquire()
        util.log("Packet Timeout! Resending Packet {}".format(seq_num))
        # Reset Timer: Only Reset if the timer is still within the timer list
        # Possible concurrency problems
        if seq_num in self.timers.keys():
            # Stop and Reset Timer
            self.timers[seq_num].cancel()
            self.timers[seq_num] = self.set_timer(seq_num)

            # Resend Packet, Start Timer
            sliding_point = seq_num % config.WINDOW_SIZE
            resend_pkt = self.msg_window[sliding_point]
            util.log("Resending Packet...")
            self.network_layer.send(resend_pkt)
            self.timers[seq_num].start()
        self.send_lock.release()
        return
