//
//  EAEExxtractorConnection.h
//  AudioEverywhereSDK
//
//  Created by Paula Chavarría on 10/22/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEConnectionResponse.h"
#import "EAEExxtractorAPIConstants.h"
#import "EAEConnectionConstants.h"
#import "EAEProfile.h"
#import "EAEProfileMenu.h"
#import "EAEReceiverProfile.h"
#import <CoreBluetooth/CoreBluetooth.h>

@protocol EAEExxtractorStreamRequesting;
@protocol EAEDiscoveredVenuePolling;
@protocol EAEDiscovering;
@protocol EAEExxtractorLocationRequesting;
@protocol EAEExxtractorDocumentRequesting;
@protocol EAEExxtractorContentRequesting;
@protocol EAEExxtractorAuthenticationRequesting;
@protocol EAEExxtractorStatsRequesting;
@protocol EAEExxtractorChannelRequesting;
@protocol EAEExxtractorProfileRequesting;
@protocol EAEExxtractorServerRequesting;


@class EAEExxtractorWebService;
@class EAEFeaturesHelper;
@class EAEAudioChannel;
@class EAELocation;
@class BARestAdapter;

extern NSString * const kEAEAppStoreUrlKey;

@interface EAEExxtractorConnection : NSObject

@property (assign, nonatomic,readonly) NSInteger activeAudioChannelIndex;
@property (strong, nonatomic) NSString *baseURL;
@property (strong, nonatomic,readonly) EAEAudioChannel* activeAudioChannel;
@property (strong, nonatomic,readonly) NSArray* audioChannels;
@property (assign, nonatomic,readonly) BOOL isBusy;
@property (strong, nonatomic,readonly) NSArray* featuredContents;
@property (strong, nonatomic,readonly) EAEFeaturesHelper *featureVerifier;
@property (nonatomic) EAEExxtractorConnectionState state;
@property (strong, nonatomic) NSString *version;
@property (strong, nonatomic, readonly) NSString *partnerUniqueIdentifier;
@property (strong, nonatomic, readonly) NSString *exxtractorUniqueIdentifier;
@property (nonatomic) BOOL demoModeEnabled;
@property (nonatomic) BOOL isDemoInTransition;
@property (nonatomic) BOOL displayPrivateChannels;
@property (nonatomic) BOOL isProfilesAvailable;
@property (nonatomic) BOOL profileNeedsUpdate;
@property (nonatomic, strong) NSString *isAdminEnabled;
@property (strong, nonatomic) EAEProfileServer *activeServer;
@property (strong, nonatomic) EAEProfile *activeProfile;
@property (nonatomic) long *activeProfileVersion;
@property (strong, nonatomic) NSString *activeProfileLeid;
@property (strong, nonatomic) NSString *triggerIdFromLink;
@property (strong, nonatomic) NSArray *docsFromProfile;
@property (strong, nonatomic) NSArray *offersFromProfile;
@property (nonatomic, strong) NSString *tokenForAdmin;
@property (assign, nonatomic) BOOL isInternetReachable;
@property (strong, nonatomic) NSMutableDictionary *debugInfoSet;
@property (strong, nonatomic) NSMutableDictionary *connectedServers;
//multi language
@property (strong, nonatomic) NSString *languageSelected;
//beacons
@property (strong, nonatomic, readonly) NSString *triggerIdFromBeacon;
@property (assign, nonatomic) BOOL executedOnce; //for loading files in operator mode
//operator mode
@property (assign, nonatomic) BOOL isOperatorModeAvailable;
@property (nonatomic) BOOL isAutomated;

//PA status
@property (nonatomic) BOOL streamingIsPA;
//bluetooth handling
@property (nonatomic, strong) CBCentralManager *centralManager;



- (id) initWithMainStreamWebService:(EAEExxtractorWebService<EAEExxtractorStreamRequesting> *) mainStreamWebService
             channelsPollingService:(id<EAEDiscoveredVenuePolling>) discoveredVenuePolling
                   discoveryService:(id<EAEDiscovering>) discoveryService
                 locationWebservice:(EAEExxtractorWebService<EAEExxtractorLocationRequesting>*)locationWebservice
                 documentWebservice:(EAEExxtractorWebService<EAEExxtractorDocumentRequesting>*)documentWebservice
                  contentWebservice:(EAEExxtractorWebService<EAEExxtractorContentRequesting>*)contentWebservice
                    statsWebservice:(EAEExxtractorWebService<EAEExxtractorStatsRequesting>*)statsWebservice
                  channelWebservice:(EAEExxtractorWebService<EAEExxtractorChannelRequesting>*)channelWebservice
                  authenticationWebservice:(EAEExxtractorWebService<EAEExxtractorAuthenticationRequesting>*)authenticationWebservice
                  profileWebservice:(EAEExxtractorWebService<EAEExxtractorProfileRequesting>*) profileWebservice
                   serverWebservice:(EAEExxtractorWebService<EAEExxtractorServerRequesting>*) serverWebservice
              connectionRestAdapter:(BARestAdapter *) connectionRestAdapter;

+ (EAEExxtractorConnection *) exxtractorConnectionWithPartnerUniqueIdentifier:(NSString *)partnerUniqueIdentifier
                                                                     loglevel: (EAEExxtractorConnectionLogLevel) logLevel;
+ (instancetype) sharedExxtractorConnection;

- (void) scanWithTimeout: (int) timeout
                 success: (EAEConnectionSuccessResponse) success
                 failure: (EAEConnectionFailureResponse) failure;
- (void) connectToVenueServer: (NSString *) targetVenueServer
                  withTimeout: (int) timeout
                  triggerIdFL: (NSString *) triggerIdFL
                      success:(EAEConnectionSuccessResponse) success
                      failure: (EAEConnectionFailureResponse) failure;

- (void) startChannelPlaybackWithChannel: (EAEAudioChannel *) channel
                   playStereoIfAvailable: (BOOL) playStereoIfAvailable
                                 success: (EAEConnectionSuccessResponse) success
                                 failure: (EAEConnectionFailureResponse) failure;

- (void) stopChannelPlaybackWithSuccess: (EAEConnectionSuccessResponse) success
                                failure: (EAEConnectionFailureResponse) failure;

- (void) validatePrivateChannelsAndSync: (NSError **) error;

- (void) validateProfilesAndSync: (EAEConnectionSuccessResponse) success
                         failure: (EAEConnectionFailureResponse) failure;

- (void) adminLogin: (NSString*) password
                         success: (EAEConnectionSuccessResponse) success
                         failure: (EAEConnectionFailureResponse) failure;

- (void) operatorLogin: (NSString*) password
              username: (NSString*) username
            success:(EAEConnectionSuccessResponse) success
            failure: (EAEConnectionFailureResponse) failure;

- (void)adminLogout:(NSString*) token
            success: (EAEConnectionSuccessResponse) success
            failure: (EAEConnectionFailureResponse) failure;


- (void) updateChannelsPrivacy: (NSArray*) channels
                        isPrivate: (BOOL) isPrivate
                        passphrase: (NSString*) passphrase
                        success: (EAEConnectionSuccessResponse) success
                        failure: (EAEConnectionFailureResponse) failure;

- (void) startSyncingChannelsWithExxtractor: (NSError **) error
                                isPrivateChannelsEnabled: (BOOL) isPrivateChannelsEnabled
                             isAdminEnabled: (NSString*) isAdminEnabled;
                            

- (void) startSyncingProfileWithExxtractor: (EAEConnectionSuccessResponse) success
                                   failure: (EAEConnectionFailureResponse) failure;

//get profiles menu
- (EAEProfileMenu*) getProfilesMenu: (EAEConnectionSuccessResponse) success
                                            failure: (EAEConnectionFailureResponse) failure;

- (EAEProfile*) startSyncingProfilesAllExxtractors: (EAEConnectionSuccessResponse) success
                                   failure: (EAEConnectionFailureResponse) failure
                              indexToInsert: (NSInteger) index;

- (void) getLocationWithSuccess: (EAEConnectionSuccessResponse) success
                        failure: (EAEConnectionFailureResponse) failure;

- (void) getDocumentsWithSuccess: (EAEConnectionSuccessResponse) success
                         failure: (EAEConnectionFailureResponse) failure;

- (void) getOffersWithSuccess: (EAEConnectionSuccessResponse) success
                      failure: (EAEConnectionFailureResponse) failure;

- (void) stopAndResetManager;

- (void) restartPlayback: (BOOL) playStereoIfAvailable;

- (void) dialogEnhacementShouldBeEnabled: (BOOL) enabled;

- (void) disconnectWithNotification: (NSString*) notificationName
                           demoMode:(BOOL) isDemoModeEnabled;
- (void) disconnect;

- (BOOL) isExxtractorConnected;

- (BOOL) isLoudSpeakerActive;
- (void) enableLoudSpeaker: (BOOL)enable;

- (NSArray *) getDocumentsFromDic:(NSMutableDictionary *) dictOfFiles;

- (void) setupLocationManager;

-(void) getServerGeneralInfo: (NSString *) baseUrlString
                     success: (EAEConnectionSuccessResponse) success
                     failure: (EAEConnectionFailureResponse) failure;

-(void) getServerUnitFile: (NSString *) baseUrlString
                    token: token
                  success: (EAEConnectionSuccessResponse) success
                 failure: (EAEConnectionFailureResponse) failure;

-(void) getServerVenueConfigFile: (NSString *) baseUrlString
                    token: (NSString *) token
                    success: (EAEConnectionSuccessResponse) success
                         failure: (EAEConnectionFailureResponse) failure;

-(EAEProfile*) getMobileAppProfile: (NSString *) baseUrlString
                    profileId: (NSString *) profileId
                    success: (EAEConnectionSuccessResponse) success
                           failure: (EAEConnectionFailureResponse) failure;

-(void) getAllFilesForOperatorMode;

- (void) updateCompleteUnitFile;
- (double) getEstimatedJitter;
- (int32_t) getEstimatedBufferSize;

#pragma mark - Profile methods

- (void) getDocumentsFromProfile;

//Multi-language
- (NSArray*) audioLanguagesFromProfiles:(NSString*) defaultDeviceLang;

- (NSString*) getChannelIdFromTrigger: (NSString *) triggerId
                        curentProfile: (EAEProfile *) profile;

#pragma mark - Operator Mode methods
- (void) updateChannelsPrivacyOperatorMode: (NSArray*) channels
                                    isPrivate: (BOOL) isPrivate
                                passphrase: (NSString*) passphrase;

#pragma mark - Connection history methods
- (void) saveConnection:(NSString *) serverConnection;
- (NSArray *) getConnections;
- (void) clearConnections;

#pragma mark - Bluetooth Manager
-(void) initBluetoothManager;

#pragma mark - PA status
- (void)checkPAAudioStream;

@end
