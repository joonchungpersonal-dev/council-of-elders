/**
 * Council of Elders — Electron main process.
 */

const { app, BrowserWindow, Menu, shell, session } = require('electron');
const path = require('path');
const { startFlask, shutdownFlask, getFlaskPort } = require('./flask-backend');

let mainWindow = null;

function createWindow(port) {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    backgroundColor: '#ffffff',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      spellcheck: true,
      preload: path.join(__dirname, '..', 'preload', 'preload.js'),
    },
  });

  win.loadURL(`http://127.0.0.1:${port}/desktop`);

  // Spellcheck context menu — provides spelling suggestions on right-click
  win.webContents.on('context-menu', (_event, params) => {
    const menuItems = [];

    // Spelling suggestions
    if (params.misspelledWord) {
      for (const suggestion of params.dictionarySuggestions.slice(0, 5)) {
        menuItems.push({
          label: suggestion,
          click: () => win.webContents.replaceMisspelling(suggestion),
        });
      }
      if (params.dictionarySuggestions.length > 0) {
        menuItems.push({ type: 'separator' });
      }
      menuItems.push({
        label: 'Add to Dictionary',
        click: () => win.webContents.session.addWordToSpellCheckerDictionary(params.misspelledWord),
      });
      menuItems.push({ type: 'separator' });
    }

    // Standard edit actions for editable fields
    if (params.isEditable) {
      menuItems.push({ role: 'cut' });
      menuItems.push({ role: 'copy' });
      menuItems.push({ role: 'paste' });
      menuItems.push({ role: 'selectAll' });
    } else if (params.selectionText) {
      menuItems.push({ role: 'copy' });
    }

    if (menuItems.length > 0) {
      Menu.buildFromTemplate(menuItems).popup();
    }
  });

  // Handle downloads — show native save dialog
  win.webContents.session.on('will-download', (_event, item) => {
    const filename = item.getFilename() || 'council_podcast.mp3';
    item.setSavePath(require('path').join(app.getPath('downloads'), filename));
  });

  win.once('ready-to-show', () => {
    win.show();
  });

  // Track main window for macOS activate behavior
  if (!mainWindow) mainWindow = win;
  win.on('closed', () => {
    if (mainWindow === win) mainWindow = null;
  });

  return win;
}

function buildMenu() {
  const isMac = process.platform === 'darwin';

  const template = [
    // App menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    }] : []),

    // File
    {
      label: 'File',
      submenu: [
        {
          label: 'New Window',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            const port = getFlaskPort();
            if (port) createWindow(port);
          },
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' },
      ],
    },

    // Edit
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },

    // View
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },

    // Window
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' },
        ] : [
          { role: 'close' },
        ]),
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(async () => {
  buildMenu();

  try {
    const port = await startFlask();
    createWindow(port);
  } catch (err) {
    console.error('Failed to start Flask backend:', err);
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      const port = getFlaskPort();
      if (port) createWindow(port);
    }
  });
});

app.on('window-all-closed', async () => {
  await shutdownFlask();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async () => {
  await shutdownFlask();
});
