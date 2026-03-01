//
//  EAEReceiverProfileMeta.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>


@interface EAEReceiverProfileMeta : NSObject

@property (strong, nonatomic) NSString * le_control_version;
@property (strong, nonatomic) NSString * profile_leid;
@property (strong, nonatomic) NSString * profile_name;
@property (assign, nonatomic) long profile_version;
@property (strong, nonatomic) NSString * venue_leid;
@property (strong, nonatomic) NSString * venue_name;

@end

