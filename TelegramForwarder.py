import time
import asyncio
from telethon.sync import TelegramClient
from datetime import datetime
from telethon.errors import FloodWaitError

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def list_chats(self):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        # Get a list of all the dialogs (chats)
        dialogs = await self.client.get_dialogs()
        chats_file = open(f"chats_of_{self.phone_number}.txt", "w")
        # Print information about each chat
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")
            chats_file.write(f"Chat ID: {dialog.id}, Title: {dialog.title} \n")
          

        print("List of groups printed successfully!")

    async def forward_messages_to_channel(self, source_chat_id, destination_channel_id, keywords):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))

        last_message_id = (await self.client.get_messages(source_chat_id, limit=1))[0].id

        while True:
            print("Checking for messages and forwarding them...")
            # Get new messages since the last checked message
            messages = await self.client.get_messages(source_chat_id, min_id=last_message_id, limit=None)

            for message in reversed(messages):
                # Check if the message text includes any of the keywords
                if keywords:
                    if message.text and any(keyword in message.text.lower() for keyword in keywords):
                        print(f"Message contains a keyword: {message.text}")

                        # Forward the message to the destination channel
                        await self.client.send_message(destination_channel_id, message.text)

                        print("Message forwarded")
                else:
                        # Forward the message to the destination channel
                        await self.client.send_message(destination_channel_id, message.text)

                        print("Message forwarded")


                # Update the last message ID
                last_message_id = max(last_message_id, message.id)

            # Add a delay before checking for new messages again
            await asyncio.sleep(5)  # Adjust the delay time as needed

    # Copy messages from the channel
    async def copy_messages(self, source_chat_id, destination_chat_id):
        await self.client.connect()
        try:
            # Use get_input_entity to ensure proper Peer usage
            source_entity = await self.client.get_input_entity(source_chat_id)
            destination_entity = await self.client.get_input_entity(destination_chat_id)
            messages_to_forward = []
            batch_size = 50
            delay_between_batches = 3  # Slightly longer delay to avoid floodwait

            print(f"Starting to copy messages from {source_entity} to {destination_entity}...")

            async for message in self.client.iter_messages(source_entity, reverse=True, offset_date=datetime(2025, 5, 31)):
                messages_to_forward.append(message.id)

                if len(messages_to_forward) >= batch_size:
                    try:
                        await self.client.forward_messages(
                            entity=destination_entity,
                            from_peer=source_entity,
                            messages=messages_to_forward
                        )
                        print(f"Forwarded batch of {len(messages_to_forward)} messages.")
                        messages_to_forward = []
                        await asyncio.sleep(delay_between_batches)
                    except FloodWaitError as e:
                        print(f"FloodWaitError: Waiting for {e.seconds} seconds.")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"Error forwarding batch: {e}")

            # Forward any remaining messages
            if messages_to_forward:
                try:
                    await self.client.forward_messages(
                        entity=destination_entity,
                        from_peer=source_entity,
                        messages=messages_to_forward
                    )
                    print(f"Forwarded final batch of {len(messages_to_forward)} messages.")
                except FloodWaitError as e:
                    print(f"FloodWaitError on final batch: Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Error forwarding final batch: {e}")

            print("Finished copying messages!")

        except Exception as e:
            print(f"Error getting history: {e}")


# Function to read credentials from file
def read_credentials():
    try:
        with open("credentials.txt", "r") as file:
            lines = file.readlines()
            api_id = lines[0].strip()
            api_hash = lines[1].strip()
            phone_number = lines[2].strip()
            return api_id, api_hash, phone_number
    except FileNotFoundError:
        print("Credentials file not found.")
        return None, None, None

# Function to write credentials to file
def write_credentials(api_id, api_hash, phone_number):
    with open("credentials.txt", "w") as file:
        file.write(api_id + "\n")
        file.write(api_hash + "\n")
        file.write(phone_number + "\n")

async def main():
    # Attempt to read credentials from file
    api_id, api_hash, phone_number = read_credentials()

    # If credentials not found in file, prompt the user to input them
    if api_id is None or api_hash is None or phone_number is None:
        api_id = input("Enter your API ID: ")
        api_hash = input("Enter your API Hash: ")
        phone_number = input("Enter your phone number: ")
        # Write credentials to file for future use
        write_credentials(api_id, api_hash, phone_number)

    forwarder = TelegramForwarder(api_id, api_hash, phone_number)
    
    print("Choose an option:")
    print("1. List Chats")
    print("2. Forward Messages")
    print("3. Copy Messages")
    
    choice = input("Enter your choice: ")
    
    if choice == "1":
        await forwarder.list_chats()
    elif choice == "2":
        source_chat_id = int(input("Enter the source chat ID: "))
        destination_channel_id = int(input("Enter the destination chat ID: "))
        print("Enter keywords if you want to forward messages with specific keywords, or leave blank to forward every message!")
        keywords = input("Put keywords (comma separated if multiple, or leave blank): ").split(",")
        
        await forwarder.forward_messages_to_channel(source_chat_id, destination_channel_id, keywords)
    elif choice == "3":
        source_chat_id = int(input("Enter the source chat ID: "))
        destination_channel_id = int(input("Enter the destination chat ID: "))
        
        await forwarder.copy_messages(source_chat_id, destination_channel_id)
 
    else:
        print("Invalid choice")


# Start the event loop and run the main function
if __name__ == "__main__":
    asyncio.run(main())
