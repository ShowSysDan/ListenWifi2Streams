//
//  EAELocation.h
//  AudioEverywhereSDK
//
//  Created by Miguel Hernandez on 8/13/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@class EAESkin;
@class EAEAdvertisement;
@class EAELocationDetail;
@class EAEProfile;

@interface EAELocation : NSObject

@property (strong,nonatomic) EAEAdvertisement *ad;
@property (strong,nonatomic) EAELocationDetail *detail;
@property (strong,nonatomic) EAESkin *skin;

- (id) initDemoLocationForPartnerId: (NSString *) partnerId;
- (id) initLocationFromProfile: (EAEProfile *) profile;

@end
