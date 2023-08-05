import sys
from typing import Tuple

from slixmpp import ClientXMPP


class MyXMPPClient(ClientXMPP):
    def __init__(self, jid, password):
        super(MyXMPPClient, self).__init__(jid, password)

        self.add_event_handler("session_start", self.handler_session_start)
        self.add_event_handler("message", self.handler_message)

    def handler_session_start(self, event):
        self.send_presence()
        self.get_roster()
        print(f"Connected to server!")

    def handler_message(self, msg):
        print(f"Received message XML:\n{msg}")
        print(f"Message from: {msg.get_from()}")
        print(f"Message type: {msg.get_type()}")
        print(f"Message body: {msg['body']}")

    def send_message_to(self, addressee: str, message: str):
        # msg = self.make_message(mto=addressee, mtype="chat", mbody=message)

        # The longer way to make message
        msg = self.Message()
        msg.set_to(addressee)
        msg.set_type("chat")
        msg["body"] = message

        print(f"Message to send XML:\n{msg}")
        msg.send()


if __name__ == "__main__":
    address: Tuple[str, int] = None
    # address = ("server_ip", 5222)  # Optional; only if the server address different with domain

    my_jid: str = input("JID     : ")
    my_password: str = input("Password: ")

    client = MyXMPPClient(my_jid, my_password)
    client.connect(address=address)
    client.process(timeout=2)

    role = input("Role (Sender/Receiver): ").upper()
    if role in ("S", "Sender"):
        try:
            while True:
                destination = input("JID Destination: ")
                message = input("Message: ")
                client.send_message_to(destination, message)
                client.process(timeout=2)
        except KeyboardInterrupt:
            print("Exiting...")
    elif role in ("R", "Receiver"):
        client.process(forever=True)
    else:
        print(f"Role invalid!")
        sys.exit(1)
