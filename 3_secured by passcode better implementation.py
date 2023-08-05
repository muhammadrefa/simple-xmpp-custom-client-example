#!/usr/bin/env python

import base64
import hashlib
import sys
from typing import Tuple

from slixmpp import ClientXMPP
from slixmpp import ElementBase, Message, register_stanza_plugin


class PayloadHeart(ElementBase):
    name = "inside-heart"
    namespace = "mr"
    plugin_attrib = "heart"
    interfaces = {"content", "is_secured", "checksum"}
    sub_interfaces = {"content", "checksum"}
    bool_interfaces = {"is_secured"}


class MyXMPPClient(ClientXMPP):
    def __init__(self, jid, password):
        super(MyXMPPClient, self).__init__(jid, password)
        self._passcode_to_try = list()

        self.add_event_handler("session_start", self.handler_session_start)
        self.add_event_handler("message", self.handler_message)

    @staticmethod
    def encrypt_message(message: bytes, key: bytes) -> bytes:
        cipher = bytearray(message)
        for msg_idx in range(0, len(cipher)):
            for key_idx in range(0, len(key)):
                try:
                    cipher[msg_idx+key_idx] ^= key[key_idx]
                except IndexError:
                    break
        return bytes(cipher)

    @staticmethod
    def decrypt_message(cipher: bytes, key: bytes) -> bytes:
        message = bytearray(cipher)
        for msg_idx in range(0, len(message)):
            for key_idx in range(0, len(key)):
                try:
                    message[msg_idx+key_idx] ^= key[key_idx]
                except IndexError:
                    break
        return bytes(message)

    def add_passcode_possibility(self, passcode: str):
        self._passcode_to_try.append(passcode)

    def handler_session_start(self, event):
        self.send_presence()
        self.get_roster()
        print(f"Connected to server!")

    def handler_message(self, msg):
        print(f"Received message XML:\n{msg}")
        # print(f"Received message val:\n{msg.values}")
        print(f"Message from: {msg.get_from()}")
        print(f"Message type: {msg.get_type()}")
        print(f"Message body: {msg['body']}")
        if msg["heart"]['content']:
            if msg["heart"]["is_secured"]:
                print(f"Secured by passcode!")
                passcode_found = False
                for passcode in self._passcode_to_try:
                    print(f"Trying [{passcode}] as passcode...")

                    content = self.decrypt_message(base64.b64decode(msg['heart']['content']), passcode.encode())
                    m = hashlib.sha256()
                    m.update(content)

                    # Passcode valid if the checksum of the decrypted message valid
                    # which means the messages are the same
                    if m.digest() == base64.b64decode(msg['heart']['checksum']):
                        print(f"Passcode valid!")
                        print(f"Real message: {content.decode()}")
                        passcode_found = True
                        break
                    else:
                        print(f"Wrong passcode!")
                if not passcode_found:
                    print("Failed to reveal real message!")
            else:
                print(f"Real message: {msg['heart']['content']}")

    def send_message_to(self, addressee: str, message: str, real_msg: str = None, passcode: str = None):
        # msg = self.make_message(mto=addressee, mtype="chat", mbody=message)

        # The longer way to make message
        msg = self.Message()
        msg.set_to(addressee)
        msg.set_type("chat")
        msg["body"] = message

        # Enable and fill our custom payload
        if real_msg:
            if passcode:
                m = hashlib.sha256()
                m.update(real_msg.encode())
                cipher = self.encrypt_message(real_msg.encode(), passcode.encode())
                msg["heart"]["is_secured"] = True
                msg["heart"]["content"] = base64.b64encode(cipher).decode()         # Content: Cipher (base64)
                msg["heart"]["checksum"] = base64.b64encode(m.digest()).decode()    # Checksum: Checksum of msg (base64)
            else:
                msg["heart"]["content"] = real_msg

        print(f"Message to send XML:\n{msg}")
        msg.send()


if __name__ == "__main__":
    address: Tuple[str, int] = None
    # address = ("server_ip", 5222)  # Optional; only if the server address different with domain

    my_jid: str = input("JID     : ")
    my_password: str = input("Password: ")

    register_stanza_plugin(Message, PayloadHeart)
    client = MyXMPPClient(my_jid, my_password)
    client.connect(address=address)
    client.process(timeout=2)

    role = input("Role (Sender/Receiver): ").upper()
    if role in ("S", "Sender"):
        try:
            while True:
                destination = input("JID Destination: ")
                message = input("Message: ")
                real_msg = input("Real message: ")
                passcode = input("Passcode (empty for none): ")
                if not passcode:
                    passcode = None
                client.send_message_to(destination, message, real_msg, passcode)
                client.process(timeout=2)
        except KeyboardInterrupt:
            print("Exiting...")
    elif role in ("R", "Receiver"):
        finished = False
        while not finished:
            passcode = input("Enter passcode possibility (empty to finish): ")
            if passcode:
                client.add_passcode_possibility(passcode)
            else:
                finished = True
        print("Now processing client...")
        client.process(forever=True)
    else:
        print(f"Role invalid!")
        sys.exit(1)
