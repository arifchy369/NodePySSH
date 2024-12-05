const WebSocket = require('ws');
const pty = require('node-pty');

const PORT = process.env.PORT || 8080;
const uname = "test@user";
const pwd = "test_pass";

class PersistentConsole {
  constructor(ws) {
    this.ptyProcess = pty.spawn('/bin/bash', ['-l'], {
      name: 'xterm-color',
      cols: 80,
      rows: 30,
      cwd: process.env.HOME,
      env: { ...process.env, PS1: '[\\u@\\h \\W] $ ' }
    });

    this.ptyProcess.on('data', (data) => {
      ws.send(JSON.stringify({ type: 'output', data }));
    });
  }

  executeCharacter(char) {
    this.ptyProcess.write(char);
  }

  resize(cols, rows) {
    this.ptyProcess.resize(cols, rows);
  }

  close() {
    this.ptyProcess.kill();
  }
}

const server = new WebSocket.Server({ port: PORT });

server.on('connection', (ws) => {
  console.log("Client connected, waiting for authentication");

  let authenticated = false;
  let consoleSession = null;

  ws.on('message', (message) => {
    if (!authenticated) {
      // Parse login credentials
      try {
        const { username, password } = JSON.parse(message);
        if (username === uname && password === pwd) {
          authenticated = true;
          ws.send(JSON.stringify({ type: 'auth', status: 'success' }));
          console.log("Client authenticated");

          // Start console session after authentication
          consoleSession = new PersistentConsole(ws);
        } else {
          ws.send(JSON.stringify({ type: 'auth', status: 'failure' }));
          ws.close();
        }
      } catch (err) {
        ws.send(JSON.stringify({ type: 'auth', status: 'failure' }));
        ws.close();
      }
    } else {
      // Handle terminal messages
      const { type, data } = JSON.parse(message);
      if (type === 'input') {
        consoleSession.executeCharacter(data);
      } else if (type === 'resize') {
        consoleSession.resize(data.cols, data.rows);
      }
    }
  });

  ws.on('close', () => {
    console.log("Client disconnected");
    if (consoleSession) {
      consoleSession.close();
    }
  });

  ws.on('error', (err) => {
    console.error("WebSocket error:", err);
    if (consoleSession) {
      consoleSession.close();
    }
  });
});

console.log(`WebSocket server running on port ${PORT}`);
