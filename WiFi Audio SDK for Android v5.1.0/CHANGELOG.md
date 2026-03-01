
# Version 5.1.0 (2025-04-16)
Changes:
- Support for solicitation packages.
- Removed ICMP for session validation.
- Improvements for PA status report.
- Improvements for playback services.

# Version 5.0.1 (2024-09-16)
Changes:
- Beacon triggering functionality
- Fix issues related with profiles
- Update target SDK version to level 34 (Android 14)

# Version 4.6.1 (2023-09-26)
Changes:
- Guava dependency was update in the SDK and was changed to implementation level.
- Update target SDK version to level 33 (Android 13)

# Version 4.5.2 (2022-10-22)
Bug fixes:
- Fix for bluetooth devices disconnection.

# Version 4.5.1 (2022-10-12)
Changes:
- Support for loudspeaker/earpiece audio play.
- Permission handling for Android 12.

# Version 4.4.1 (2022-06-15)
Changes:
- Update target SDK version to level 31 (Android 12).
- Support for Android 12.

# Version 4.3 (2022-01-13)
Changes:
- 1020 changes

# Version 4.2.2 (2021-12-10)
Bug fixes:
- Fixed issue related with Audio is distorted on Private Channel

# Version 4.2.1 (2021-11-17)
Changes:
- Update target SDK version to level 30 (Android 11).
- Support for HTTPS
- Use of new and more secure encryption method for private channels
Bug fixes:
- Fixed issue with DELETE method for streaming
- Fixed issue related to close socket after stop streaming

# Version 4.1 (2021-10-08)
Changes:
- Minimum SDK changed from 14 to 16 (raises minimum Android from 4.0 to 4.1) 
Bugfixes:
- Fixed issue causing freezing when server resource is unavailable
- Fixed issue causing app to take a long time to go to scan screen when lost connection
- Fixed issue causing options set to private to take a long time to propagate to the app
- Fixed issue causing higher latency on certain android devices
- Fixed issue causing lock screen controls to not appear on Android 11 and 12
- Fixed issue causing “waiting for audio” message to continue even after audio is re-established
- Fixed issue causing audio to pause when connecting headphones
- Fixed issue causing audio pause to occasionally trigger disconnections from server

# Version 3.3.2 (2020-08-20)
- HTTPS support for private channels.

# Version 3.2.2 (2020-07-20)
- Add support for private channels.

# Version 3.2.0 (2020-06-09)
- Update target SDK version to level 29 (Android 10).
- Reduce the number of transitive dependencies.

# Version 3.1.5 (2020-02-26)
- Recompile code with latest SDK version API level 29 (Android 10).
- Add missing permission to execute foreground services.

# Version 3.1.4 (2019-09-20)
- Avoid restarting audio after transient audio loss as it causes a crash on the
app.

# Version 3.1.3 (2019-09-18)
- The device’s IPv4 address information is updated when connecting via direct
connection or dynamic links to avoid issues when the WiFi network is changed.

# Version 3.1.2 (2019-07-23)
- Prevent Android Manager Leak on pre-Android N(24) versions, by initializing
- WiFi Manager via the application context
- Removing unused keys on resource files.
- Including missing translations for resources (Required on Android API 28)

# Version: 3.1.1
- Only broadcast media button events that are handled by the SDK, and ignore the ones not supported, to prevent app crashes.
- Ensure native libraries are built in a way such that target API is set lower than the device API, to prevent API level 23 devices using armeabi to crash when attempting to load dependencies.
