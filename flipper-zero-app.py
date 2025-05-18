# Smart451 CAN Sniffer - Flipper Zero App

App(
    appid="smart451_can",
    name="Smart451 CAN",
    apptype=FlipperAppType.EXTERNAL,
    entry_point="smart451_can_app",
    stack_size=2 * 1024,
    fap_category="Tools",
    fap_icon="images/can_icon_10px.png",
    fap_icon_assets="images",
    fap_author="Smart451",
    fap_weburl="https://github.com/yourusername/flipper-smart451",
    fap_version=(0, 1),
    fap_description="CAN bus sniffer and decoder for Smart 451 ForTwo",
)

# Smart451 CAN Sniffer - Main Application Code

import furi
import os
import struct
import time
import threading
from furi import Resource
from furi.ui import Canvas, Widget, ViewDispatcher
from furi.ui.button import Button
from furi.ui.screen import ScreenManager
from furi.ui.view import View

# CAN frame format
class CANFrame:
    def __init__(self, id=0, ext=False, rtr=False, dlc=0, data=None):
        self.id = id
        self.is_extended = ext
        self.is_rtr = rtr
        self.dlc = dlc
        self.data = data or bytearray(8)
        self.timestamp = int(time.time() * 1000)

# ESP32 UART Communication
class ESP32Interface:
    def __init__(self, rx_callback=None):
        self.serial = furi.io.Serial()
        self.rx_callback = rx_callback
        self.buffer = ""
        self.connected = False
        
    def connect(self):
        try:
            self.serial.open("usart_ext", 115200)
            self.connected = True
            # Start receiver thread
            self.rx_thread = threading.Thread(target=self._rx_task)
            self.rx_thread.daemon = True
            self.rx_thread.start()
            return True
        except Exception as e:
            print(f"Error connecting to ESP32: {e}")
            return False
            
    def disconnect(self):
        if self.connected:
            self.connected = False
            self.serial.close()
            
    def send_command(self, cmd):
        if not self.connected:
            return False
        try:
            self.serial.write(f"{cmd}\n".encode())
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
            
    def _rx_task(self):
        while self.connected:
            try:
                data = self.serial.read(1)
                if data:
                    char = data.decode()
                    if char == '\n':
                        if self.rx_callback:
                            self.rx_callback(self.buffer)
                        self.buffer = ""
                    else:
                        self.buffer += char
            except Exception as e:
                print(f"RX error: {e}")
                time.sleep(0.1)

# CAN Data Storage
class CANDatabase:
    def __init__(self):
        self.frames = {}  # id -> list of frames
        self.known_ids = {}  # id -> description
        self.latest_values = {}  # id -> latest value
        
    def add_frame(self, frame):
        if frame.id not in self.frames:
            self.frames[frame.id] = []
        
        # Keep max 100 frames per ID
        if len(self.frames[frame.id]) >= 100:
            self.frames[frame.id].pop(0)
            
        self.frames[frame.id].append(frame)
        
    def get_frames(self, id=None):
        if id is None:
            # Return all frames flattened
            result = []
            for frames in self.frames.values():
                result.extend(frames)
            return sorted(result, key=lambda f: f.timestamp)
        elif id in self.frames:
            return self.frames[id]
        else:
            return []
            
    def get_ids(self):
        return sorted(self.frames.keys())
        
    def set_known_id(self, id, description):
        self.known_ids[id] = description
        
    def get_description(self, id):
        return self.known_ids.get(id, "Unknown")
        
    def set_latest_value(self, id, value):
        self.latest_values[id] = value
        
    def get_latest_value(self, id):
        return self.latest_values.get(id, None)

# Main Application View
class CANSnifferView(View):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = app.db
        self.selected_id = None
        self.scroll_pos = 0
        self.view_mode = "list"  # "list" or "detail"
        
    def input(self, input_type, input_event):
        if input_type == Button.Type.SHORT:
            if input_event == Button.Right:
                if self.view_mode == "list":
                    ids = self.db.get_ids()
                    if ids and self.selected_id is None:
                        self.selected_id = ids[0]
                    elif ids:
                        idx = ids.index(self.selected_id)
                        if idx < len(ids) - 1:
                            self.selected_id = ids[idx + 1]
                elif self.view_mode == "detail":
                    self.scroll_pos += 1
                self.update()
                return True
                
            elif input_event == Button.Left:
                if self.view_mode == "list":
                    ids = self.db.get_ids()
                    if ids and self.selected_id is None:
                        self.selected_id = ids[-1]
                    elif ids:
                        idx = ids.index(self.selected_id)
                        if idx > 0:
                            self.selected_id = ids[idx - 1]
                elif self.view_mode == "detail":
                    if self.scroll_pos > 0:
                        self.scroll_pos -= 1
                self.update()
                return True
                
            elif input_event == Button.Ok:
                if self.view_mode == "list" and self.selected_id is not None:
                    self.view_mode = "detail"
                    self.scroll_pos = 0
                elif self.view_mode == "detail":
                    self.view_mode = "list"
                self.update()
                return True
                
            elif input_event == Button.Back:
                if self.view_mode == "detail":
                    self.view_mode = "list"
                    self.update()
                    return True
                else:
                    # Exit application
                    return False
        
        return False
                
    def draw(self, canvas):
        canvas.clear()
        canvas.set_font("primary")
        
        if self.view_mode == "list":
            self._draw_list_view(canvas)
        else:
            self._draw_detail_view(canvas)
            
    def _draw_list_view(self, canvas):
        canvas.draw_str(0, 10, "Smart 451 CAN Sniffer")
        canvas.draw_line(0, 12, 128, 12)
        
        ids = self.db.get_ids()
        if not ids:
            canvas.draw_str(0, 24, "No CAN frames received")
            canvas.draw_str(0, 36, "Check connections...")
            return
            
        y = 24
        for i, id in enumerate(ids):
            if i < self.scroll_pos:
                continue
                
            if y > 64:
                break
                
            selected = (id == self.selected_id)
            if selected:
                canvas.draw_rect(0, y-10, 128, 12, fill=True)
                canvas.set_color(0, 0, 0)
                
            desc = self.db.get_description(id)
            if len(desc) > 15:
                desc = desc[:12] + "..."
                
            text = f"0x{id:03X} : {desc}"
            canvas.draw_str(0, y, text)
            
            if selected:
                canvas.set_color(1, 0, 0)
                
            y += 12
            
        # Draw scroll indicator
        if len(ids) > 4:
            scroll_height = min(64 / len(ids) * 4, 64)
            scroll_pos = min(64 - scroll_height, 64 * self.scroll_pos / len(ids))
            canvas.draw_rect(127, scroll_pos, 1, scroll_height, fill=True)
            
    def _draw_detail_view(self, canvas):
        if not self.selected_id:
            return
            
        id = self.selected_id
        frames = self.db.get_frames(id)
        
        canvas.draw_str(0, 10, f"ID: 0x{id:03X}")
        canvas.draw_line(0, 12, 128, 12)
        
        desc = self.db.get_description(id)
        canvas.draw_str(0, 24, f"Desc: {desc}")
        
        if not frames:
            canvas.draw_str(0, 36, "No frames")
            return
            
        frame = frames[-1]  # Latest frame
        
        canvas.draw_str(0, 36, f"DLC: {frame.dlc}  {'EXT' if frame.is_extended else 'STD'}")
        
        # Draw data bytes
        y = 48
        data_str = "Data: "
        for i in range(min(8, frame.dlc)):
            if i % 4 == 0 and i > 0:
                canvas.draw_str(0, y, data_str)
                data_str = "      "
                y += 12
            data_str += f"{frame.data[i]:02X} "
            
        canvas.draw_str(0, y, data_str)

# Status Bar View
class StatusBarView(View):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
    def draw(self, canvas):
        # Draw at the bottom of the screen
        canvas.set_font("primary")
        
        # Status indicators
        esp_status = "ESP: " + ("OK" if self.app.esp.connected else "X")
        count = len(self.app.db.get_ids())
        id_count = f"IDs: {count}"
        
        canvas.draw_str(0, 62, esp_status)
        canvas.draw_str(64, 62, id_count)

# Main Application
class Smart451CANApp:
    def __init__(self):
        self.db = CANDatabase()
        self.esp = ESP32Interface(rx_callback=self._on_esp_message)
        
        # Load known IDs for Smart 451
        self._load_known_ids()
        
        # Set up UI
        self.view_dispatcher = ViewDispatcher()
        self.main_view = CANSnifferView(self)
        self.status_bar = StatusBarView(self)
        
        self.view_dispatcher.add_view("main", self.main_view)
        self.view_dispatcher.add_view("status", self.status_bar)
        
    def on_start(self):
        # Connect to ESP32
        self.esp.connect()
        self.esp.send_command("HELLO")
        
        # Load known IDs from ESP
        self.esp.send_command("GETKNOWNIDS")
        
        # Start the UI
        self.view_dispatcher.switch_to("main")
        
    def on_stop(self):
        self.esp.disconnect()
        
    def run(self):
        self.on_start()
        
        # Run the UI
        self.view_dispatcher.run()
        
        self.on_stop()
        
    def _on_esp_message(self, message):
        if message.startswith("CAN:"):
            # Parse CAN frame
            parts = message.split(":")
            if len(parts) >= 5:
                try:
                    id = int(parts[1], 16)
                    ext = parts[2] == "1"
                    rtr = parts[3] == "1"
                    dlc = int(parts[4])
                    
                    data = bytearray(8)
                    if len(parts) > 5 and parts[5]:
                        data_parts = parts[5].split()
                        for i, hex_byte in enumerate(data_parts):
                            if i < 8:
                                data[i] = int(hex_byte, 16)
                    
                    frame = CANFrame(id, ext, rtr, dlc, data)
                    self.db.add_frame(frame)
                    
                    # Update UI
                    self.main_view.update()
                    self.status_bar.update()
                except Exception as e:
                    print(f"Error parsing CAN frame: {e}")
                    
        elif message.startswith("ACK GETKNOWNIDS"):
            # Parse known IDs
            try:
                count = int(message.split()[2])
                for _ in range(count):
                    # Wait for more messages with ID info
                    pass
            except Exception as e:
                print(f"Error parsing known IDs: {e}")
                
    def _load_known_ids(self):
        # Preload some known Smart 451 IDs
        known_ids = {
            0x175: "Engine RPM",
            0x280: "Vehicle Speed",
            0x307: "Engine Temperature",
            0x470: "Door Status",
            0x500: "Lights Status",
            0x608: "Fuel Level",
            0x710: "Gear Status"
        }
        
        for id, desc in known_ids.items():
            self.db.set_known_id(id, desc)

def smart451_can_app(params):
    app = Smart451CANApp()
    app.run()
    return 0

if __name__ == "__main__":
    # For running directly on a PC for testing
    class TestApp:
        def __init__(self):
            self.db = CANDatabase()
            self.esp = ESP32Interface(rx_callback=self._on_esp_message)
        
        def _on_esp_message(self, message):
            print(f"Received: {message}")
    
    app = TestApp()
