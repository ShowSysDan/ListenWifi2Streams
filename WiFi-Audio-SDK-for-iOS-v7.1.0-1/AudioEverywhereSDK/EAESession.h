//
//  EAESession.h
//  AudioEverywhereSDK
//
//  Created by Raul Gomez on 8/18/20.
//  Copyright (c) 2020 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAESession : NSObject

@property (strong, nonatomic) NSString *token;
@property (strong, nonatomic) NSString *name;
@property (strong, nonatomic) NSNumber* level;

@end
