//
//  EAEReceiverProfile.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEReceiverProfileMeta.h"
#import "EAEReceiverProfileSetting.h"
#import "EAEReceiverProfileInfrastructure.h"

@interface EAEReceiverProfile : NSObject
@property (strong, nonatomic) EAEReceiverProfileMeta* meta;
@property (strong, nonatomic) EAEReceiverProfileSetting* settings;
@property (strong, nonatomic) NSArray* audio_options;
@property (strong, nonatomic) EAEReceiverProfileInfrastructure* infrastructure;
@property (strong, nonatomic) NSArray* automations;
@end

