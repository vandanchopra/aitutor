#!/usr/bin/env python3
"""
Python MediaMixer - Combines camera, screen share, and scratchpad streams
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import mss
import time
import base64
import io
from typing import Optional, Callable
import os
import asyncio
import websockets

import json


class MediaMixer:
    """Combines camera, screen share, and scratchpad streams"""
    
    def __init__(self, 
                 output_width: int = 1280, 
                 output_height: int = 2160,
                 fps: int = 15,
                 on_mixed_frame: Optional[Callable[[str], None]] = None):
        
        self.output_width = output_width
        self.output_height = output_height
        self.fps = fps
        self.on_mixed_frame = on_mixed_frame
        self.scratchpad_frame: Optional[np.ndarray] = None
        
        # Section dimensions (each section is 1280x720)
        self.section_width = output_width
        self.section_height = output_height // 3
        
        # Initialize components
        self.camera = None
        try:
            self.screen_capture = mss.mss()
            print("Screen capture initialized successfully")
        except Exception as e:
            self.screen_capture = None
            print(f"Could not initialize screen capture: {e}")
        
        # Control flags
        self.running = False
        self.show_preview = False
        self.show_camera = False
        self.show_screen = False
        
        # Initialize camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize camera capture"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("Warning: Could not open camera")
                self.camera = None
            else:
                # Set camera resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                print("Camera initialized successfully")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
    
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """Capture frame from camera"""
        if not self.camera or not self.show_camera:
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # Resize to section dimensions
        frame = cv2.resize(frame, (self.section_width, self.section_height))
        return frame
    
    def get_screen_frame(self) -> Optional[np.ndarray]:
        """Capture screen frame"""
        if not self.show_screen:
            return None
        try:
            # Get the primary monitor
            monitor = self.screen_capture.monitors[1]  # 0 is all monitors, 1 is primary
            
            # Capture screen
            screenshot = self.screen_capture.grab(monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR (remove alpha channel)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            # Resize to section dimensions
            frame = cv2.resize(frame, (self.section_width, self.section_height))
            
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def mix_frames(self, scratchpad_current: Optional[np.ndarray] = None) -> np.ndarray:
        """Mix all three video sources into a single frame"""
        # Create output canvas
        mixed_frame = np.zeros((self.output_height, self.output_width, 3), dtype=np.uint8)
        
        # Get frames from all sources
        if scratchpad_current is None:
            # Create a blank white frame
            scratchpad_frame = np.ones((self.section_height, self.section_width, 3), dtype=np.uint8) * 255
        else:
            scratchpad_frame = cv2.resize(scratchpad_current, (self.section_width, self.section_height))

        screen_frame = self.get_screen_frame()
        camera_frame = self.get_camera_frame()
        
        # Section 1: Scratchpad (always present)
        y_offset = 0
        mixed_frame[y_offset:y_offset + self.section_height, :] = scratchpad_frame
        
        # Section 2: Screen share (if available)
        y_offset = self.section_height
        if screen_frame is not None:
            mixed_frame[y_offset:y_offset + self.section_height, :] = screen_frame
        else:
            # Fill with black if no screen share
            mixed_frame[y_offset:y_offset + self.section_height, :] = 0
        
        # Section 3: Camera (if available)
        y_offset = 2 * self.section_height
        if camera_frame is not None:
            mixed_frame[y_offset:y_offset + self.section_height, :] = camera_frame
        else:
            # Fill with dark gray if no camera
            mixed_frame[y_offset:y_offset + self.section_height, :] = 64
        
        return mixed_frame
    
    def frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert OpenCV frame to base64 JPEG string"""
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        # Convert to base64
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        return base64_data
    
    def stop(self):
        """Stop the mixer and cleanup resources"""
        self.running = False
        
        if self.camera:
            self.camera.release()
        
        cv2.destroyAllWindows()
        print("MediaMixer stopped")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop()

async def handler(websocket):
    print(f"Client connected: {websocket.remote_address}")
    mixer = MediaMixer()
    mixer.running = True
    
    # Check if we should enable camera and screen by default
    # (when run through tutor script or with AUTO_ENABLE env var)
    if os.environ.get('MEDIAMIXER_AUTO_ENABLE') == '1' or __name__ == '__main__':
        mixer.show_camera = True
        mixer.show_screen = True
        print("✅ Camera and screen sharing enabled by default")

    async def send_frames():
        while mixer.running:
            try:
                mixed_frame = mixer.mix_frames(scratchpad_current=mixer.scratchpad_frame)
                base64_frame = mixer.frame_to_base64(mixed_frame)
                await websocket.send(base64_frame)
                await asyncio.sleep(1/mixer.fps)
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected")
                mixer.running = False
                break
            except Exception as e:
                print(f"Error in send_frames: {e}")
                mixer.running = False
                break

    async def receive_commands():
        while mixer.running:
            try:
                message = await websocket.recv()
                try:
                    # Assume message is a JSON string
                    data = json.loads(message)
                    if data.get('type') == 'scratchpad_frame':
                        base64_data = data['data'].split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        # Convert RGB from browser to BGR for OpenCV
                        mixer.scratchpad_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                except json.JSONDecodeError:
                    # Message is not JSON, treat as a simple command
                    if message == "start_camera":
                        mixer.show_camera = True
                    elif message == "stop_camera":
                        mixer.show_camera = False
                    elif message == "start_screen":
                        mixer.show_screen = True
                    elif message == "stop_screen":
                        mixer.show_screen = False

            except websockets.exceptions.ConnectionClosed:
                mixer.running = False
                break
            except Exception as e:
                print(f"Error processing message: {e}")

    send_task = asyncio.create_task(send_frames())
    receive_task = asyncio.create_task(receive_commands())

    await asyncio.gather(send_task, receive_task)

async def main():
    try:
        print("Starting MediaMixer WebSocket server...")
        async with websockets.serve(handler, "localhost", 8765):
            print("✅ WebSocket server started on ws://localhost:8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        print(f"❌ Error starting MediaMixer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🚀 MediaMixer starting up...")
    try:
        # When running as main, enable camera and screen by default
        original_handler = handler
        async def main_handler(websocket):
            print(f"Client connected: {websocket.remote_address}")
            mixer = MediaMixer()
            mixer.running = True
            # Enable camera and screen by default when running as main
            mixer.show_camera = True
            mixer.show_screen = True
            print("✅ Camera and screen sharing enabled by default")

            async def send_frames():
                while mixer.running:
                    try:
                        mixed_frame = mixer.mix_frames(scratchpad_current=mixer.scratchpad_frame)
                        base64_frame = mixer.frame_to_base64(mixed_frame)
                        await websocket.send(base64_frame)
                        await asyncio.sleep(1/mixer.fps)
                    except websockets.exceptions.ConnectionClosed:
                        print("Client disconnected")
                        mixer.running = False
                        break
                    except Exception as e:
                        print(f"Error in send_frames: {e}")
                        mixer.running = False
                        break

            async def receive_commands():
                while mixer.running:
                    try:
                        message = await websocket.recv()
                        try:
                            # Assume message is a JSON string
                            data = json.loads(message)
                            if data.get('type') == 'scratchpad_frame':
                                base64_data = data['data'].split(',')[1]
                                img_bytes = base64.b64decode(base64_data)
                                img = Image.open(io.BytesIO(img_bytes))
                                # Convert RGB from browser to BGR for OpenCV
                                mixer.scratchpad_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        except json.JSONDecodeError:
                            # Message is not JSON, treat as a simple command
                            if message == "start_camera":
                                mixer.show_camera = True
                            elif message == "stop_camera":
                                mixer.show_camera = False
                            elif message == "start_screen":
                                mixer.show_screen = True
                            elif message == "stop_screen":
                                mixer.show_screen = False

                    except websockets.exceptions.ConnectionClosed:
                        mixer.running = False
                        break
                    except Exception as e:
                        print(f"Error processing message: {e}")

            send_task = asyncio.create_task(send_frames())
            receive_task = asyncio.create_task(receive_commands())

            await asyncio.gather(send_task, receive_task)
        
        # Override the handler for main execution
        globals()['handler'] = main_handler
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Fatal error in MediaMixer: {e}")
        import traceback
        traceback.print_exc()