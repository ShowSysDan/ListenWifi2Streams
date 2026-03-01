//
//  EAEDebugInformation.h
//  AudioEverywhereSDK
//
//  Created by Elena Delgado on 29/11/23.
//  Copyright © 2023 Listen Technologies Corporation. All rights reserved.
//

#import <Foundation/Foundation.h>


@interface EAEDebugInformation : NSObject

@property (strong, nonatomic) NSString* triggerId;
@property (strong, nonatomic) NSString* channelId;
@property (assign, nonatomic) int threshold;
@property (assign, nonatomic) int strength;
@property (assign, nonatomic) bool overrideEngaged;
@property (assign, nonatomic) long exitTimeout;
@property (assign, nonatomic) long countdown;

@end
