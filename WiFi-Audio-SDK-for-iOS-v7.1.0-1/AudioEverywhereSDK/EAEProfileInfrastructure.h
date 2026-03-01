//
//  EAEProfileInfrastructure.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 8/12/22.
//  Copyright © 2022 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfileServer.h"

@interface EAEProfileInfrastructure : NSObject
@property (strong, nonatomic) NSArray* servers;
@property (assign, nonatomic) NSArray* gps;
@property (assign, nonatomic) NSArray* timers;
@end
