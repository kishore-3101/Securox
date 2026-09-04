import os
import sys
import asyncio

# Change working directory to backend so database paths load correctly
os.chdir('backend')
sys.path.append('.')
import main

async def test():
    # CAM_6E62783B is the Living Room Tapo
    generator = main.mjpeg_stream_generator("CAM_6E62783B")
    
    try:
        chunk = await generator.__anext__()
        print(f"Retrieved first chunk of size {len(chunk)} bytes.")
        
        start = chunk.find(b'\xff\xd8')
        end = chunk.find(b'\xff\xd9', start)
        if start != -1 and end != -1:
            jpeg_bytes = chunk[start:end+2]
            # Save in backend parent folder
            with open("../scratch/test_stream_frame.jpg", "wb") as f:
                f.write(jpeg_bytes)
            print("Successfully saved frame to scratch/test_stream_frame.jpg")
        else:
            print("Could not find JPEG markers in chunk.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
