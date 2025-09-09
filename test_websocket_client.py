#!/usr/bin/env python3
"""
Simple test harness for testing WebSocket codeUpdated events.
"""

import asyncio
import json
import time
import websockets
import jwt
from pathlib import Path
from sidekick import __version__

# Configuration
SERVER_URL = "ws://localhost:43001"
TENANT = "test_company"
PROJECT_ID = "test_project"
WORKSPACE_DIR = Path("~/.aistudio").expanduser()
FUNCTIONS_FILE = WORKSPACE_DIR / "projects" / TENANT / PROJECT_ID / "functions.py"

def create_jwt_token(tenant: str, project_id: str, sidekick_version: str) -> str:
    """Create a JWT token with the required claims."""
    payload = {
        "tenant": tenant,
        "projectId": project_id,
        "sidekickVersion": sidekick_version,
        "iat": int(time.time()),  # Issued at time
        "exp": int(time.time()) + 3600  # Expires in 1 hour
    }

    # For testing, we'll use a simple secret (in production this should be secure)
    secret = "test-secret-key"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

async def test_websocket_client():
    """Test WebSocket client that sends a message and listens for responses."""

    # Create JWT token
    jwt_token = create_jwt_token(TENANT, PROJECT_ID, __version__)

    # Construct WebSocket URL (no query parameters)
    ws_url = f"{SERVER_URL}/ws"

    # Create sub-protocol header
    subprotocol = f"sidekick-{jwt_token}"

    print(f"🔌 Connecting to: {ws_url}")
    print(f"🎫 Using sub-protocol: sidekick-<jwt_token>")
    print(f"📁 Expected file location: {FUNCTIONS_FILE}")
    print()

    try:
        # Connect to WebSocket with sub-protocol
        async with websockets.connect(ws_url, subprotocols=[subprotocol]) as websocket:
            print("✅ WebSocket connected successfully!")
            print("👂 Listening for messages... (Press Ctrl+C to exit)")
            print()

            # Prepare test code
            test_code = '''def hello_world():
    """A simple test function."""
    print("Hello from Sidekick WebSocket test!")
    return "success"

def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

# Test variables
TEST_MESSAGE = "This code was sent via WebSocket!"
'''

            # Create codeUpdated message
            message = {
                "type": "codeUpdated",
                "payload": {
                    "code": test_code,
                    "timestamp": int(time.time() * 1000)
                }
            }

            print(f"📤 Sending initial codeUpdated message...")
            print(f"   Code length: {len(test_code)} characters")
            print(f"   Timestamp: {message['payload']['timestamp']}")

            # Send the message
            await websocket.send(json.dumps(message))
            print("✅ Message sent successfully!")
            print()

            # Wait a moment for the server to process
            await asyncio.sleep(1)

            # Check if file was created/updated
            if FUNCTIONS_FILE.exists():
                actual_content = FUNCTIONS_FILE.read_text()
                if actual_content == test_code:
                    print("🎉 SUCCESS: File was created/updated correctly!")
                    print(f"   File location: {FUNCTIONS_FILE}")
                    print(f"   File size: {len(actual_content)} characters")
                else:
                    print("❌ FAILURE: File content doesn't match sent code")
                    print(f"   Expected length: {len(test_code)}")
                    print(f"   Actual length: {len(actual_content)}")
            else:
                print("❌ FAILURE: File was not created")
                print(f"   Expected location: {FUNCTIONS_FILE}")

            print()
            print("📋 Now you can:")
            print(f"   1. Edit the file: {FUNCTIONS_FILE}")
            print("   2. Watch for incoming messages below")
            print("   3. Press Ctrl+C to exit")
            print()
            print("📥 Incoming messages:")
            print("-" * 40)

            # Listen for incoming messages indefinitely
            message_count = 0
            async for message in websocket:
                message_count += 1
                timestamp = time.strftime("%H:%M:%S")

                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "unknown")
                    payload = data.get("payload", {})

                    print(f"[{timestamp}] Message #{message_count}")
                    print(f"  Type: {msg_type}")

                    if msg_type == "codeUpdated":
                        code = payload.get("code", "")
                        msg_timestamp = payload.get("timestamp", "")
                        print(f"  Code length: {len(code)} characters")
                        print(f"  Timestamp: {msg_timestamp}")
                        print(f"  First 100 chars: {repr(code[:100])}")
                    else:
                        print(f"  Payload: {payload}")

                    print()

                except json.JSONDecodeError:
                    print(f"[{timestamp}] Raw message: {message}")
                    print()

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        if e.code == 1008:
            print("   This might be a version mismatch error")
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the test."""
    print("🧪 Sidekick WebSocket Test Harness")
    print("=" * 50)
    print(f"Server: {SERVER_URL}")
    print(f"Tenant: {TENANT}")
    print(f"Project: {PROJECT_ID}")
    print(f"Version: {__version__}")
    print("=" * 50)
    print()

    print("📋 Instructions:")
    print("1. Make sure Sidekick server is running:")
    print("   sidekick")
    print("2. Run this test script:")
    print("   python test_websocket_client.py")
    print("3. Edit the functions.py file to test bidirectional sync")
    print()

    # Run the test
    asyncio.run(test_websocket_client())

if __name__ == "__main__":
    main()