//
//  EAEProfileMeta.h
//  ListenEverywhere
//
//  Created by Raul Gomez on 4/6/21.
//  Copyright (c) 2021 Listen Technologies Inc. All rights reserved.
//
#import <Foundation/Foundation.h>

@interface EAEProfileMeta : NSObject
@property (strong, nonatomic) NSString * profile_leid;
@property (strong, nonatomic) NSString * profile_name;
@property (assign, nonatomic) long profile_version;
@property (strong, nonatomic) NSString * venue_name;
@property (strong, nonatomic) NSString * venue_leid;
@property (strong, nonatomic) NSString * le_control_version;

@end
