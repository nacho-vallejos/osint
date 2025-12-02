"""
WebSocket Router for Real-time Scan Updates
Provides WebSocket endpoints for receiving live scan progress and results.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import logging
import os

from app.core.socket_manager import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/scan/{task_id}")
async def websocket_scan_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time scan updates.
    
    Clients connect to this endpoint with a task_id and receive live updates
    as the scan progresses, without needing to poll the REST API.
    
    Args:
        websocket: FastAPI WebSocket connection
        task_id: The Celery task ID to monitor
        
    Flow:
        1. Client connects: ws://localhost:8000/ws/scan/{task_id}
        2. Server accepts and subscribes to Redis channel: scan_updates:{task_id}
        3. As Celery worker publishes updates, they're forwarded to client
        4. When scan completes (SUCCESS/FAILURE), connection can close
        
    Example JavaScript client:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/ws/scan/abc123...');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Update:', data);
            if (data.status === 'SUCCESS') {
                // Handle complete result
                ws.close();
            }
        };
        ```
    """
    manager = get_connection_manager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    
    try:
        # Accept connection and start listening
        await manager.connect(websocket, task_id)
        logger.info(f"WebSocket connection established for task: {task_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "task_id": task_id,
            "message": "WebSocket connected. Waiting for scan updates..."
        })
        
        # Keep connection alive and listen for client messages
        # (though we mainly push data from Redis, not receive from client)
        try:
            while True:
                # Wait for any message from client (or just keep alive)
                data = await websocket.receive_text()
                logger.debug(f"Received from client on task {task_id}: {data}")
                
                # Optionally handle client commands
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from task {task_id}")
    
    except Exception as e:
        logger.error(f"Error in WebSocket connection for task {task_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"WebSocket error: {str(e)}"
            })
        except Exception:
            pass
    
    finally:
        # Cleanup connection
        await manager.disconnect(websocket, task_id)
        logger.info(f"WebSocket cleanup complete for task {task_id}")


@router.get("/ws/test")
async def websocket_test_page():
    """
    Test page for WebSocket connections.
    Useful for manual testing and debugging.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Scan Updates Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            .container {
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 8px;
            }
            input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: #45a049;
            }
            button.disconnect {
                background: #f44336;
            }
            button.disconnect:hover {
                background: #da190b;
            }
            #messages {
                margin-top: 20px;
                padding: 10px;
                background: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
                height: 400px;
                overflow-y: auto;
            }
            .message {
                padding: 8px;
                margin: 5px 0;
                border-radius: 4px;
            }
            .message.success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
            }
            .message.error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
            }
            .message.info {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
            }
            .status {
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
                display: inline-block;
                margin: 10px 0;
            }
            .status.connected {
                background: #d4edda;
                color: #155724;
            }
            .status.disconnected {
                background: #f8d7da;
                color: #721c24;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔌 WebSocket Scan Updates Test</h1>
            
            <div>
                <label>Task ID:</label>
                <input type="text" id="taskId" placeholder="Enter task ID from /api/v1/scan">
                
                <button onclick="connect()">Connect</button>
                <button class="disconnect" onclick="disconnect()">Disconnect</button>
                <button onclick="clearMessages()">Clear Messages</button>
            </div>
            
            <div>
                <span>Status: </span>
                <span id="status" class="status disconnected">Disconnected</span>
            </div>
            
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                const taskId = document.getElementById('taskId').value;
                if (!taskId) {
                    alert('Please enter a task ID');
                    return;
                }
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/scan/${taskId}`;
                
                addMessage('Connecting to: ' + wsUrl, 'info');
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    addMessage('✅ WebSocket connected!', 'success');
                    updateStatus(true);
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    addMessage(JSON.stringify(data, null, 2), 'info');
                    
                    // Auto-close on completion
                    if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
                        addMessage(`Scan ${data.status}. Auto-closing...`, 'success');
                        setTimeout(() => disconnect(), 2000);
                    }
                };
                
                ws.onerror = (error) => {
                    addMessage('❌ WebSocket error: ' + error, 'error');
                };
                
                ws.onclose = () => {
                    addMessage('Connection closed', 'info');
                    updateStatus(false);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function addMessage(msg, type = 'info') {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = new Date().toLocaleTimeString() + ' - ' + msg;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function updateStatus(connected) {
                const statusSpan = document.getElementById('status');
                statusSpan.textContent = connected ? 'Connected' : 'Disconnected';
                statusSpan.className = 'status ' + (connected ? 'connected' : 'disconnected');
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/ws/health")
async def websocket_health():
    """
    Health check for WebSocket service.
    Returns information about active connections.
    """
    manager = get_connection_manager()
    
    return {
        "status": "healthy",
        "service": "websocket",
        "active_tasks": len(manager.active_connections),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "listener_tasks": len(manager.listener_tasks)
    }
