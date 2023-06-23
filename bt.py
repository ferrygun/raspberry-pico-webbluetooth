import asyncio
from bleak import BleakScanner, BleakClient

device = None
write_characteristic = None
read_characteristic = None

async def connect_to_device():
    global device, write_characteristic, read_characteristic
    try:
        print('Requesting Bluetooth Device...')

        if device and device.is_connected:
            print('Already connected to device')
            #await send_message()
            return

        scanner = BleakScanner()
        await scanner.start()

        await asyncio.sleep(2)  # Allow time for scanning

        connected = False
        while not connected:
            devices = scanner.discovered_devices

            for dev in devices:
                if dev.name == 'mpy-uart':
                    device = BleakClient(dev)
                    try:
                        await device.connect()
                        connected = True
                        break
                    except:
                        pass

        print('Connecting to GATT Server...')

        if device is not None:
            await device.connect()

            services = device.services

            for service in services:
                if str(service.uuid) == '6e400001-b5a3-f393-e0a9-e50e24dcca9e':
                    characteristics = service.characteristics

                    for char in characteristics:
                        if str(char.uuid) == '6e400002-b5a3-f393-e0a9-e50e24dcca9e':
                            write_characteristic = char

                        if str(char.uuid) == '6e400003-b5a3-f393-e0a9-e50e24dcca9e':
                            read_characteristic = char

        print('Enabling notifications...')

        if device is not None and read_characteristic is not None and write_characteristic is not None:
            await device.start_notify(read_characteristic.uuid, handle_data)

            print('Connected to device')

            # Start sending a message
            await send_message()
    except Exception as error:
        print('Error: ' + str(error))

def handle_data(sender: int, data: bytearray):
    value = bytes(data)
    decoder = 'utf-8'
    decoded_data = value.decode(decoder)
    print('Received: ' + decoded_data)

async def send_message():
    try:
        message = input('Enter message to send: ')
        encoder = 'utf-8'
        encoded_data = message.encode(encoder)

        if write_characteristic is not None:
            await device.write_gatt_char(write_characteristic, encoded_data)
            print('Sent: ' + message)
        else:
            print('Write characteristic not found.')
    except Exception as error:
        print('Error: ' + str(error))

async def main():
    while True:
        await connect_to_device()
        await asyncio.sleep(5)  # Wait for 5 seconds before retrying the connection

# Run the main coroutine
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
