# 📺Multi-functional Real-time Video Conferencing System with Client-Server and P2P Architecture

## Project Overview

This project aims to build an online video conferencing platform compatible with both Client-Server (CS) and Peer-to-Peer (P2P) architectures. The platform integrates various features, including user screen splitting, online video, voice communication, text communication, and screen sharing, to provide users with an efficient, stable, and feature-rich real-time communication experience.

## Functional Modules

### 1. User Screen Splitting

- **Description**: Supports multiple users participating in video conferences simultaneously, with each user occupying an independent split-screen area for easy viewing and interaction.
- **Technical Implementation**: Achieves dynamic split-screen display through front-end layout management combined with CSS Grid.

### 2. Online Video

- **Description**: Provides high-quality real-time video communication, supporting multiple resolutions and frame rates to ensure smooth and clear video.
- **Technical Implementation**: Realized through front-end and back-end Flask-SocketIO interaction and server-client multi-threaded data forwarding.

### 3. Voice Communication

- **Description**: Supports real-time voice communication, allowing users to toggle mute/unmute freely, with clear and stable voice quality.
- **Technical Implementation**: Achieved using WebRTC's audio module, combined with echo cancellation and noise suppression technologies to enhance voice quality.

### 4. Text Communication

- **Description**: Provides real-time text chat functionality, enabling users to send and receive text messages during meetings, with support for emojis and file sharing.
- **Technical Implementation**: Uses the WebSocket protocol for real-time text message transmission, with the back-end handling message push via Flask-SocketIO.

### 5. Screen Sharing

- **Description**: Supports screen sharing, allowing users to share their screen content in real-time with other participants for demonstrations and collaboration.
- **Technical Implementation**: Achieved using WebRTC's screen sharing API for screen capture and transmission, supporting multiple screen resolutions and refresh rates.

## Technical Architecture

### 1. Communication Protocols

- **TCP Protocol**: Used for establishing stable connections and transmitting control signals and critical data.
- **UDP Protocol**: Used for transmitting real-time video and audio data to reduce latency and improve communication efficiency.
- **HTTP Protocol**: Used for initial connections and data exchange between the front-end and back-end.
- **WebSocket Protocol**: Used for real-time communication between the front-end and back-end, supporting bidirectional data transmission.

### 2. Back-end Technologies

- **Flask Framework**: Serves as the back-end server framework, providing RESTful APIs and WebSocket services.
- **Flask-SocketIO Extension**: Used for WebSocket communication, supporting real-time message push and event handling.
- **Cross-Origin Resource Sharing (CORS)**: Enables cross-origin requests, ensuring seamless interaction between the front-end and back-end.
- **JSON Data Format**: Uses JSON for front-end and back-end interactions to ensure efficient and readable data transmission.

### 3. Front-end Technologies

- **Vue.js Framework**: Used for building the user interface, providing reactive data binding and component-based development.
- **Vite Build Tool**: Used for rapid development and packaging, supporting Hot Module Replacement (HMR) to enhance development efficiency.
- **CSS Preprocessor**: Uses SCSS or LESS to improve the maintainability of style code.
- **Layout Management**: Implements dynamic layouts using CSS Grid or Flexbox to adapt to various screen sizes.

## System Design

### 1. Architecture Design

- **Client-Server Architecture**: The back-end server acts as a central node, responsible for user authentication, message distribution, and resource management.
- **P2P Architecture**: Establishes direct connections between users to reduce server load and improve communication efficiency.
- **Hybrid Architecture**: Combines the advantages of CS and P2P architectures, dynamically switching based on network conditions to ensure system stability and efficiency.

### 2. Multi-threading and Asynchronous Technologies

- **Multi-threading**: The back-end server uses multi-threading to handle user requests, improving concurrent processing capabilities.
- **Asynchronous Processing**: Both the front-end and back-end use asynchronous technologies (e.g., JavaScript's Promise and async/await) to reduce blocking and enhance user experience.

## Development Process

### 1. Requirement Analysis

- Analyze user requirements and define system functional modules and performance metrics.
- Design the system architecture and select the appropriate technology stack.

### 2. Front-end Development

- Use Vue.js and Vite to build the user interface and implement functional modules.
- Optimize front-end performance to ensure fast and smooth interface responsiveness.

### 3. Back-end Development

- Use the Flask framework to set up the back-end service and implement WebSocket communication.
- Integrate WebRTC technology to enable video and voice communication functionalities.

### 4. Testing and Optimization

- Conduct unit testing, integration testing, and stress testing to ensure system stability and reliability.
- Optimize code based on test results to improve system performance.

## Project Outcomes

Through this project, we have successfully built a multi-functional real-time video conferencing platform compatible with both CS and P2P architectures. The platform has met the expected goals in terms of functionality and performance, providing users with an efficient, stable, and feature-rich real-time communication experience. In the future, we will continue to optimize system performance, add more functional modules, and enhance the user experience.
