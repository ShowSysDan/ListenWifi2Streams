//
//  EAEReceiverProfileInfrastructure.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEReceiverProfileInfrastructure : NSObject

@property (strong, nonatomic) NSArray* servers;
@property (strong, nonatomic) NSArray* gps;
@property (strong, nonatomic) NSArray* timers;

@end


