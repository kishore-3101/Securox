import sys
import asyncio
sys.path.append('backend')
from simulation.data_generator import data_generator

async def test():
    print("Testing real-time data generator...")
    stream = data_generator.normal_stream(interval=0.1)
    
    for i in range(10):
        event = await stream.__anext__()
        print(f"\n--- Event {i+1} ---")
        print(f"Type: {event.get('type')}")
        print(f"Asset: {event.get('asset_type')}")
        print(f"Timestamp: {event.get('timestamp')}")
        
        if event.get('type') == 'iot_telemetry':
            print(f"Device: {event.get('device_id')}")
            print(f"Request Count (metric value): {event.get('request_count')}")
            print(f"Payload Bytes: {event.get('payload_bytes')}")
        elif event.get('type') == 'network_traffic':
            print(f"Connection: {event.get('src_ip')}:{event.get('src_port')} -> {event.get('dst_ip')}:{event.get('dst_port')}")
            print(f"Protocol: {event.get('protocol')}")
            print(f"Flags/Processes: {event.get('flags')}")
        elif event.get('type') == 'system_log':
            print(f"Service/Process: {event.get('service')}")
            print(f"Level: {event.get('level')}")
            print(f"Message: {event.get('message')}")

if __name__ == "__main__":
    asyncio.run(test())
