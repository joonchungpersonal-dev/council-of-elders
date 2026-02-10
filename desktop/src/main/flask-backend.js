/**
 * Flask backend process manager.
 * Finds Python venv, picks a free port, spawns Flask, polls health, shuts down.
 */

const { spawn } = require('child_process');
const path = require('path');
const net = require('net');
const http = require('http');

let flaskProcess = null;
let flaskPort = null;

/**
 * Find the Python interpreter and project root.
 * Checks two locations:
 *   1. Packaged app: Resources/ inside the .app bundle
 *   2. Dev mode: project root one level up from desktop/
 */
function findPython() {
  const fs = require('fs');
  const { app } = require('electron');

  // When packaged, extraResource copies into process.resourcesPath
  const isPackaged = app.isPackaged;
  const locations = [];

  if (isPackaged) {
    const resPath = process.resourcesPath;
    locations.push({
      python: path.join(resPath, 'venv', 'bin', 'python3'),
      projectRoot: resPath,
    });
    locations.push({
      python: path.join(resPath, 'venv', 'bin', 'python'),
      projectRoot: resPath,
    });
  }

  // Dev mode: project root is one level up from desktop/
  const devRoot = path.resolve(__dirname, '..', '..', '..');
  locations.push({ python: path.join(devRoot, 'venv', 'bin', 'python3'), projectRoot: devRoot });
  locations.push({ python: path.join(devRoot, 'venv', 'bin', 'python'), projectRoot: devRoot });

  for (const loc of locations) {
    if (fs.existsSync(loc.python)) {
      return loc;
    }
  }

  const checked = locations.map(l => l.python).join('\n');
  throw new Error(`Python venv not found. Checked:\n${checked}`);
}

/**
 * Find a free port by binding to port 0 and reading the assigned port.
 */
function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

/**
 * Spawn the Flask backend as a child process.
 */
function spawnFlask(port, python, projectRoot) {
  const env = {
    ...process.env,
    FLASK_PORT: String(port),
    PYTHONUNBUFFERED: '1',
  };

  flaskProcess = spawn(python, ['-m', 'council.web.app'], {
    cwd: projectRoot,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log(`[flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`[flask] ${data.toString().trim()}`);
  });

  flaskProcess.on('exit', (code, signal) => {
    console.log(`[flask] Process exited (code=${code}, signal=${signal})`);
    flaskProcess = null;
  });

  flaskPort = port;
  return flaskProcess;
}

/**
 * Poll the Flask health endpoint until it responds (or timeout).
 */
function waitForFlask(port, timeoutMs = 30000) {
  const start = Date.now();
  const interval = 500;

  return new Promise((resolve, reject) => {
    function poll() {
      if (Date.now() - start > timeoutMs) {
        reject(new Error(`Flask did not start within ${timeoutMs / 1000}s`));
        return;
      }

      const req = http.get(`http://127.0.0.1:${port}/api/status`, (res) => {
        let body = '';
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          if (res.statusCode === 200) {
            console.log(`[flask] Backend ready on port ${port}`);
            resolve(port);
          } else {
            setTimeout(poll, interval);
          }
        });
      });

      req.on('error', () => {
        setTimeout(poll, interval);
      });

      req.setTimeout(2000, () => {
        req.destroy();
        setTimeout(poll, interval);
      });
    }

    poll();
  });
}

/**
 * Gracefully shut down the Flask process.
 */
function shutdownFlask() {
  return new Promise((resolve) => {
    if (!flaskProcess) {
      resolve();
      return;
    }

    console.log('[flask] Sending SIGTERM...');
    flaskProcess.kill('SIGTERM');

    const forceKillTimer = setTimeout(() => {
      if (flaskProcess) {
        console.log('[flask] Force-killing with SIGKILL...');
        flaskProcess.kill('SIGKILL');
      }
    }, 3000);

    flaskProcess.on('exit', () => {
      clearTimeout(forceKillTimer);
      flaskProcess = null;
      resolve();
    });
  });
}

/**
 * Start the Flask backend: find Python, pick port, spawn, wait for health.
 * Returns the port number on success.
 */
async function startFlask() {
  const { python, projectRoot } = findPython();
  console.log(`[flask] Python: ${python}`);
  console.log(`[flask] Project root: ${projectRoot}`);

  const port = await findFreePort();
  console.log(`[flask] Using port ${port}`);

  spawnFlask(port, python, projectRoot);
  await waitForFlask(port);

  return port;
}

function getFlaskPort() {
  return flaskPort;
}

module.exports = { startFlask, shutdownFlask, getFlaskPort };
