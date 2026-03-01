//
//  EAEProfile.h
//  ListenEverywhereSDK
//
//  Created by Raul Gomez on 4/6/21.
//  Copyright (c) 2021 Listen Technologies Inc. All rights reserved.
//
#import <Foundation/Foundation.h>
#import "EAEProfileMeta.h"
#import "EAEProfileSetting.h"
#import "EAEProfileServer.h"
#import "EAEProfileAssets.h"
#import "EAEProfileInfrastructure.h"


@interface EAEProfile : NSObject
@property (strong, nonatomic) EAEProfileMeta* meta;
@property (strong, nonatomic) EAEProfileSetting* settings;
@property (strong, nonatomic) NSArray* audio_options;
@property (strong, nonatomic) EAEProfileAssets* assets;
@property (strong, nonatomic) EAEProfileInfrastructure* infrastructure;
@property (strong, nonatomic) NSArray* automations;
@end
