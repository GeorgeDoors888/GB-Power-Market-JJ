import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

# Load environment variables
load_dotenv()

# Securely get credentials
TENANT_ID = os.getenv('IRIS_TENANT_ID')
CLIENT_ID = os.getenv('IRIS_CLIENT_ID')
CLIENT_SECRET = os.getenv('IRIS_CLIENT_SECRET')
NAMESPACE = os.getenv('IRIS_NAMESPACE')
QUEUE_NAME = os.getenv('IRIS_QUEUE_NAME')

# Build fully qualified namespace
fully_qualified_namespace = f"{NAMESPACE}.servicebus.windows.net"

# Authenticate
credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

# Connect to Service Bus and receive messages
with ServiceBusClient(fully_qualified_namespace, credential) as servicebus_client:
    receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
    with receiver:
        print(f"Listening for messages on queue: {QUEUE_NAME} ...")
        messages = receiver.receive_messages(max_message_count=5, max_wait_time=10)
        if not messages:
            print("No messages received.")
        for msg in messages:
            print("Received message:")
            print(str(msg))
            # Optionally, complete the message so it's removed from the queue
            receiver.complete_message(msg)
