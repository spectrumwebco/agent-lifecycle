module.exports = {
  platforms: {
    ios: {
      bundleId: 'au.com.spectrumwebco.kled',
      displayName: 'Kled.io',
      buildSettings: {
        TARGETED_DEVICE_FAMILY: '1,2', // iPhone and iPad
        DEVELOPMENT_TEAM: 'YOUR_TEAM_ID', // Replace with your Apple Developer Team ID
      }
    },
    android: {
      applicationId: 'au.com.spectrumwebco.kled',
      displayName: 'Kled.io',
      versionCode: 1,
      versionName: '0.1.0',
      targetSdkVersion: 33,
      minSdkVersion: 24
    }
  },
  shared: {
    assets: ['./assets'],
    capabilities: [
      'camera',
      'location',
      'push-notifications'
    ]
  }
};
