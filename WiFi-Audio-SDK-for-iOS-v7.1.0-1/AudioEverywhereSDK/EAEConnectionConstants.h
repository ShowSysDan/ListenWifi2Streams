//
//  EAEConnectionConstants.h
//  AudioEverywhereSDK
//
//  Created by Miguel Hernandez on 10/28/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEConnectionConstants : NSObject

enum EAEExxtractorConnectionErrorCode : NSUInteger {
    EAEExxtractorConnectionErrorCodeForUnreachableLAN = 1, // The LAN is unreachable. A scan found be performed.
    
    EAEExxtractorConnectionErrorCodeForUnavailableService = 2, // The scanned service is no longer available. A scan should be performed.
    EAEExxtractorConnectionErrorCodeForScanTimeout = 3, // The scan timeout was reached, and no services were found. A scan should be performed.
    EAEExxtractorConnectionErrorCodeForUnknownError = 4, // An unkown error ocurred. A scan should be performed.
    EAEExxtractorConnectionErrorCodeForInterruptedScan = 5, // The scan was interrupted. A scan should be performed.
    EAEExxtractorConnectionErrorCodeForNoConnectedService = 6, // An ExXtractor service connection has not been established yet. In order to do so a scan should be performed.
    EAEExxtractorConnectionErrorCodeForInvalidLocation = 7,
    EAEExxtractorConnectionErrorCodeForPrivateChannels = 8
};

typedef enum {
    EAEExxtractorConnectionStateDiscovery,
    EAEExxtractorConnectionStateConnected,
    EAEExxtractorConnectionStateConnectedPolling,
    EAEExxtractorConnectionStateIdle,
} EAEExxtractorConnectionState;

typedef enum {
    EAEExxtractorConnectionLogLevelNone,
    EAEExxtractorConnectionLogLevelFull
} EAEExxtractorConnectionLogLevel;

#pragma mark - Error description constants

extern NSString *const kEAEErrorDomain;
extern NSString *const kEAEErrorDescriptionForUnreachableLAN;
extern NSString *const kEAEErrorDescriptionForUnavailableService;
extern NSString *const kEAEErrorDescriptionForScanTimeout;
extern NSString *const kEAEErrorDescriptionForInterruptedScan;
extern NSString *const kEAEErrorDescriptionForUnknownError;
extern NSString *const kEAEErrorDescriptionForNoConnectedService;
extern NSString *const kEAEErrorDescriptionForInvalidLocation;
extern NSString *const kEAEErrorDescriptionForPrivateChannels;
extern NSString *const kEAEErrorDescriptionForAlreadyOpenSession;
#pragma mark - 
#pragma mark Error codes

extern int const kEAEErrorCodeForHTTPRequestError;
extern int const EAEExxtractorConnectionErrorCodeForAlreadyOpenSession;

#pragma mark - Notification constants

extern NSString *const kEAENotificationExxtractorConnectionWasInterrupted;
extern NSString *const kEAENotificationPlaybackWasInterrupted;
extern NSString *const kEAENotificationChannelsHaveBeenSyncedWithExxtractor;
extern NSString *const kEAENotificationNeighborsVersionsHaveBeenUpdated;
extern NSString *const kEAENotificationFeaturedContentsHaveBeenSyncedWithExxtractor;
extern NSString *const kEAENotificationLocationPermissionsChanged;
extern NSString *const kEAENotificationSessionHasEnded;
extern NSString *const kEAENotificationDemoModeIsStarted;
extern NSString *const kEAENotificationExxtractorDisconnectionByUser;
extern NSString *const kEAENotificationPrivateChannels;
extern NSString *const kEAENotificationUpdateProfile;
extern NSString *const kEAENotificationUpdateUIForChannels;
extern NSString *const kEAENotificationupdateUIChannelsOnServerStatusConection;
extern NSString *const kEAENotificationExxtractorConnectionIntermittent;
extern NSString *const kEAENotificationExxtractorConnectionRecovered;
extern NSString *const kEAENotificationExxtractorDisconnectionByInterruption;
extern NSString *const kEAENotificationChannelConfiguration;
extern NSString *const kEAENotificationProximityStateDidChange;
//PA streaming
extern NSString *const kEAENotificationPAStreamingChange;
//Beacons
extern NSString *const kEAENotificationBeaconDetection;
//Bluetooth device
extern NSString *const  kEAENotificationBluetoothDeviceDetection;
//Bluetooth enabled
extern NSString *const  kEAENotificationBluetoothDisabled;

#pragma mark - Connection history constants
extern NSString* const kEAEConnectionHistoryUserDefaultsKey;

#pragma mark -
#pragma mark Devices constants

extern NSString *const kEAEiOSDeviceiPad;
extern NSString *const kEAEiOSDeviceiPhone;

#pragma mark -
#pragma mark language constants
extern NSString *const kAEAUserDefaultLangFilter;
extern NSString *const kAEALocaleLanguageCodeKey;
extern NSString *const kAEATitleForSelectLanguage;
extern NSString *const kAEAMessageForSelectLanguage;

#pragma mark - beacons
extern NSString *const kAEAUUIDListenBeacons;
extern NSString *const kAEAIdentifierBeacons;

extern NSString *const kAEAEmptyString;
extern NSString *const kAEAGenericServerString;

#pragma mark - operator mode
extern NSString *const kAEAUserDefaultIsOperatorModeAvailable;

#pragma mark - diagnostic/debug mode
extern NSString *const kAEDebugModeActive;
extern NSString *const kAERssi;
@end
