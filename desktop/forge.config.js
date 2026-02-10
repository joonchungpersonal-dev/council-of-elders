module.exports = {
  packagerConfig: {
    name: 'Council of Elders',
    executableName: 'council-of-elders',
    asar: true,
    extraResource: ['../council', '../venv'],
    icon: undefined, // TODO: add app icon
  },
  makers: [
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin', 'linux'],
    },
    {
      name: '@electron-forge/maker-dmg',
      config: {
        format: 'ULFO',
      },
    },
  ],
};
