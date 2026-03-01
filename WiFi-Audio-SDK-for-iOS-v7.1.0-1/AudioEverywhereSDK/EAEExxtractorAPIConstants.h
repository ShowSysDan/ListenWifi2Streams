//
//  EAEExxtractorAPIConstants.h
//  AudioEverywhere
//
//  Created by Paula Chavarría on 3/13/14.
//  Copyright (c) 2014 Exxothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEExxtractorAPIConstants : NSObject

#define EXXTRACTOR_API_BASE_URL_V1 @"/api/myapp"
#define EXXTRACTOR_API_BASE_URL_V2 @"/exxtractor/api/v2"
#define EXXTRACTOR_API_BASE_URL_V3 @"/exxtractor/api/v3"
#define EXXTRACTOR_API_VERSION_V1 @"v1"
#define EXXTRACTOR_API_VERSION_V2 @"v2"
#define EXXTRACTOR_API_VERSION_V2 @"v3"

//LE Controller API
#define CONTROLLER_API_BASE_URL_V3 @"/controller/api/v3"


typedef enum {
    EAEExxtractorAPIV1 = 1,
    EAEExxtractorAPIV2 = 2
} EAEExxtractorAPIVersion;

#pragma mark -
#pragma mark Constants

extern int const kEAEAudioChannelPortForExxtractor;

#pragma mark Paths

extern NSString * const kEAEExxtractorAPIV1PathForNetworksAudioChannels;
extern NSString * const kEAEExxtractorAPIV1PathForFeaturedContent;
extern NSString * const kEAEExxtractorAPIV1PathForStream;
extern NSString * const kEAEExxtractorAPIV2PathForNetworksAudioChannels;
extern NSString * const kEAEExxtractorAPIV2PathForFeaturedContent;
extern NSString * const kEAEExxtractorAPIV2PathForStream;
extern NSString * const kEAEExxtractorAPIV3PathForStream;
extern NSString * const kEAEExxtractorAPIV2PathForLocation;
extern NSString * const kEAEExxtractorAPIV2PathForDocuments;
extern NSString * const kEAEExxtractorAPIV2PathForOffers;
extern NSString * const kEAEExxtractorAPIV2PathForLocalAudioChannels;
extern NSString * const kEAEExxtractorAPIV2PathForNeighbors;
extern NSString * const kEAEExxtractorAPIV2PathForState;
extern NSString * const kEAEExxtractorAPIV2PathForData;
extern NSString * const kEAEExxtractorAPIV2PathForLogin;
extern NSString * const kEAEExxtractorAPIV2PathForUser;
extern NSString * const kEAEExxtractorAPIV2PathForLogs;
extern NSString * const kEAEExxtractorAPIV2PathForLogout;
extern NSString * const kEAEExxtractorAPIV2PathForStat;
//API V3
extern NSString * const kEAEExxtractorAPIV3PathForPrivateAudioChannels;
extern NSString * const kEAEControllerAPIV3PathForProfiles;
extern NSString * const kEAEExxtractorAPIV3PathForLogout;
extern NSString * const kEAEControllerAPIV3PathForProfilesMenu;
extern NSString * const kEAEControllerAPIV3PathForServerInfo;
extern NSString * const kEAEExxtractorAPIV3PathForLogin;
extern NSString * const kEAEExxtractorAPIV3PathForOperatorLogin;
//profiles - receiver
extern NSString * const kEAEControllerAPIV3PathForReceiverProfiles;
//server config files
extern NSString * const kEAEControllerAPIV3PathForServerUnitFile;
//venue config file profile.json
extern NSString * const kEAEControllerAPIV3PathForServerVenueConfigFile;

#pragma mark GET Parameters

extern NSString *const kEAEExxtractorAPIGetParameterSession;
extern NSString *const kEAEExxtractorAPIGetParameterPrivateChannels;
extern NSString *const kEAEExxtractorAPIGetParameterIsAdminEnabled;
extern NSString *const kEAEExxtractorAPIDevideIdParameter;
extern NSString *const kEAEExxtractorAPIKeyParameter;
extern NSString *const kEAEExxtractorAPIProfileKeyParameter;
extern NSString *const kEAEExxtractorAPIProfileSecretKeyParameter;
extern NSString *const kEAEExxtractorAPIGetDeviceType;
extern NSString *const kEAEExxtractorAPIGetOS;
extern NSString *const kEAEExxtractorAPIGetOSValue;
extern NSString *const kEAEExxtractorAPIGetToken;
extern NSString *const kEAEExxothermicPartnerId;
extern NSString *const kEAEMyePartnerId;
extern NSString *const kEAEListenTechnologiesPartnerId;
extern NSString *const kEAEExxtractorAPIAuthorization;


#pragma mark HEADER Keys

extern NSString *const kEAEExxtractorAPIGetToken;
extern NSString *const kEAEExxtractorAPIV3PostToken;

#pragma mark -
#pragma mark Key paths

extern NSString *const kEAEExxtractorAPIKeyPathChannelInfo;
extern NSString *const kEAEExxtractorAPIKeyPathAudioStream;

#pragma mark -
#pragma mark Key timeouts

extern int const kStreamRequestTimeout;
extern int const kDnsRecordRequestTimeout;
extern int const kConnectionTimeout;
extern int const kDefaultRequestTimeout;
extern int const kOperatorLogintRequestTimeout;

#pragma mark Device types

extern NSString *const kDeviceTypeIphone;
extern NSString *const kDeviceTypeIphone5;
extern NSString *const kDeviceTypeIpad;

#pragma mark Keys

extern NSString *const venueServerKey;

#pragma mark other info for paths
extern NSString *const kEAEControllerAPIProfileDefault;

#pragma mark -
#pragma mark Custom accessors

+ (NSDictionary*) defaultHeaders;




@end
