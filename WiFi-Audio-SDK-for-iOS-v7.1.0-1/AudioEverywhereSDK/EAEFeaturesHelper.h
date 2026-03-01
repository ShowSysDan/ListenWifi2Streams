//
//  EAEFeaturesHelper.h
//  AudioEverywhereSDK
//
//  Created by Miguel Hernandez on 11/3/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEExxtractorAPIConstants.h"

@interface EAEFeaturesHelper : NSObject

@property (assign, nonatomic) NSString *version;

- (BOOL) areSomeFeaturesDisabled;
- (BOOL) areFilesEnabled;
- (BOOL) isLocationAvailable;
- (BOOL) areOffersEnabled;
- (BOOL) isPartnerInformationEnabled;
- (NSString*) getVersionWithAllFeatures;
- (BOOL) isPrivateChannelsEnabled;
- (BOOL) isProfilesAvailable;
- (BOOL) isDuplexCommunicationEnabled;
- (BOOL) isOperatorModeAvailable;
- (BOOL) isProfilesAvailable;
- (BOOL) isSHA2Available:(NSString *) serverVersion;
@end
