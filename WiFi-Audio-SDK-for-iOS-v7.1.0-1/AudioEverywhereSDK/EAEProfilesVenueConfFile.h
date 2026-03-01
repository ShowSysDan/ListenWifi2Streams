//
//  EAEProfilesVenueConfFile.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 3/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEMobileAppVenueConfFile.h"
#import "EAEReceiverVenueConfFile.h"

@interface EAEProfilesVenueConfFile : NSObject

@property (strong, nonatomic) NSArray* mobile_app;
@property (strong, nonatomic) NSArray* receiver;

@end
