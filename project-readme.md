# Smart451 Triad ESP32-S3 CAN Sniffer with Flipper Zero

This project implements a sophisticated CAN bus sniffer and decoder specifically optimized for the Smart 451 ForTwo vehicle, using a triad of ESP32-S3 microcontrollers working in harmony with a Flipper Zero. The system features advanced hardware fault tolerance, signal optimization through LC tank circuits, and machine learning-based signal decoding.

## System Architecture

### Hardware Components
- 3x ESP32-S3 microcontrollers (with machine learning capabilities)
- Flipper Zero
- MCP2515 CAN controller
- SD card for each processing unit (Flipper and ESP)
- Custom LC tank circuits for signal optimization

### Triad Mesh Network
The three ESP32-S3 modules form a fault-tolerant mesh network:
- Each runs identical firmware but with different node roles (ALPHA, BETA, GAMMA)
- Circular communication pattern where each node monitors the others
- Triad validation ensures data integrity through cross-checking
- Configurable through hardware jumpers to designate node roles

### Signal Optimization with LC Tanks
- Tunable LC tank circuits at each interconnect point
- Phase-aligned ESP-NOW communication achieved through precise spacing
- Audio feedback (via PWM) for manual tuning based on signal quality
- Self-tuning capability with real-time quality metrics

### CAN Bus Interface
- 500 kbps CAN interface for Smart 451 ForTwo
- Frame buffering and batch processing for efficiency
- SD card logging with automatic rotation for extended capture sessions
- Known parameter decoding for Smart-specific CAN IDs

## Software Components

### ESP32-S3 CAN Sniffer Core
The core module handles CAN bus communication, frame parsing, and basic logging:
- Interrupt-driven CAN frame reception
- Triad validation of incoming frames
- SD card logging with automatic file rotation
- Flipper Zero communication protocol

### ESP32-S3 Pattern Learning Module
This module implements the machine learning capabilities:
- CAN frame pattern analysis and signal extraction
- Value scaling based on known parameters
- Pattern recognition for unknown IDs
- Smart 451-specific signal database

### ESP32-S3 LC Tuning Module
Handles the optimization of inter-ESP communication:
- Phase coherence monitoring
- Signal quality assessment
- Tuning guidance via PWM tone output 
- Triad harmony status tracking

### Master Integration
Ties all components together:
- Main initialization and system orchestration
- Component integration
- Flipper Zero command handling
- Triad mesh heartbeat and status monitoring

### Flipper Zero App
Provides the user interface and control features:
- CAN traffic display and analysis
- Node status monitoring
- Command interface to the ESP32 triad
- Frame logging and export

## Getting Started

### Hardware Setup
1. Assemble the ESP32-S3 triad with proper spacing (λ/4 or 3.1cm) for phase alignment
2. Connect MCP2515 to primary ESP32-S3 (ALPHA node)
3. Install LC tank circuits at interconnection points
4. Connect Flipper Zero GPIO to primary ESP32-S3

### Configuration
1. Set node identities via hardware jumpers or in firmware
2. Update the MAC addresses in the peer configuration
3. Adjust the CAN bus speed if needed (default: 500 kbps for Smart 451)

### Installation
1. Flash the ESP32-S3 firmware to all three modules
2. Install the Smart451 app on your Flipper Zero
3. Connect to your vehicle's OBD-II port using the appropriate adapter

### Usage
1. Power on the system
2. The Flipper Zero will display the system status and CAN traffic
3. Use the Flipper interface to toggle between ID list and detailed views
4. Tune LC tanks if needed, following the audio guidance

## Technical Reference

### LC Tank Values for Key Frequencies

| Frequency   | Inductor (nH) | Capacitor (pF) | Notes                   |
|-------------|---------------|----------------|-------------------------|
| 100 kHz     | 2200          | 1000           | Low frequency CAN data  |
| 500 kHz     | 1000          | 100            | Standard CAN bus rate   |
| 1 MHz       | 470           | 47             | High speed CAN          |
| 8 MHz       | 100           | 22             | MCU clock harmonics     |
| 16 MHz      | 68            | 10             | ESP32 crystal freq      |
| 2.4 GHz     | 8.2           | 0.5            | ESP-NOW/WiFi (high tank)|
| 2.4 GHz     | 3.9           | 1.0            | ESP-NOW/WiFi (low tank) |

### Known Smart 451 CAN IDs

| ID (hex) | Description          | Units | Formula           |
|----------|----------------------|-------|-------------------|
| 0x175    | Engine RPM           | rpm   | value * 0.25      |
| 0x280    | Vehicle Speed        | km/h  | value * 0.01      |
| 0x307    | Engine Temperature   | °C    | value - 40        |
| 0x450    | Battery Voltage      | V     | value * 0.1       |
| 0x470    | Door Status          | -     | Bit mapped        |
| 0x500    | Lights Status        | -     | Bit mapped        |
| 0x608    | Fuel Level           | %     | value * 0.5       |
| 0x710    | Gear Status          | -     | Enum              |

## Future Enhancements

- Support for Smart 451 variant coding through the CAN bus
- OTA firmware updates between ESP nodes
- Enhanced machine learning for parameter auto-detection
- Integration with vehicle feature unlocking
- Battery-powered operation with power management

## License

This project is open source and available under the MIT License.
