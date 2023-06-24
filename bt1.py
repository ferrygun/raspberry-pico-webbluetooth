import sys
import asyncio
from bleak import BleakScanner, BleakClient

device = None
write_characteristic = None
read_characteristic = None

async def connect_to_device():
    global device, write_characteristic, read_characteristic
    try:
        if device and device.is_connected:
            print('Already connected to device')
            return

        scanner = BleakScanner()
        await scanner.start()
        await asyncio.sleep(2)  # Allow time for scanning
        devices = scanner.discovered_devices

        for dev in devices:
            print(dev.name)
            if dev.name == 'mpy-uart':
                device = BleakClient(dev)
                await device.connect(timeout=5)  # Set a timeout for connection
                break

        if device is None:
            print('Device not found')
            return

        print('Connecting to GATT Server...')
        if device.is_connected:  # Access is_connected as a property
            print('Already connected to GATT Server')
        else:
            await device.connect()  # Connect if not already connected

        services = device.services

        for service in services:
            if str(service.uuid) == '6e400001-b5a3-f393-e0a9-e50e24dcca9e':
                characteristics = service.characteristics

                for char in characteristics:
                    if str(char.uuid) == '6e400002-b5a3-f393-e0a9-e50e24dcca9e':
                        write_characteristic = char

                    if str(char.uuid) == '6e400003-b5a3-f393-e0a9-e50e24dcca9e':
                        read_characteristic = char

        if read_characteristic is None or write_characteristic is None:
            print('Characteristics not found')
            return

        print('Enabling notifications...')
        await device.start_notify(read_characteristic.uuid, handle_data)

        print('Connected to device')

        await send_message()
    except Exception as error:
        print('Error: ' + str(error))
        if device is not None and device.is_connected:
            await device.disconnect()

async def handle_data(sender: int, data: bytearray):
    try:
        value = bytes(data)
        decoder = 'utf-8'
        decoded_data = value.decode(decoder)
        print('Received: ' + decoded_data)
    except Exception as error:
        print('Error handling received data: ' + str(error))

async def send_message():
    try:
        prompt = input('Enter prompt (LEFT or RIGHT): ') if len(sys.argv) == 1 else sys.argv[1]
        message = 'left' if prompt.lower() == 'left' else 'right'
        encoder = 'utf-8'
        encoded_data = message.encode(encoder)

        if write_characteristic is not None:
            await device.write_gatt_char(write_characteristic, encoded_data)
            print('Sent: ' + message)
            await asyncio.sleep(1)  # Add a delay of 1 second
        else:
            print('Write characteristic not found.')
    except Exception as error:
        print('Error: ' + str(error))


async def main():
    try:
        retry_attempts = 5
        retry_interval = 1  # seconds

        for _ in range(retry_attempts):
            await connect_to_device()
            if device is not None and device.is_connected:
                break
            else:
                print('Retrying connection...')
                await asyncio.sleep(retry_interval)

    finally:
        if device is not None and device.is_connected:
            await device.disconnect()

# Run the main coroutine
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
