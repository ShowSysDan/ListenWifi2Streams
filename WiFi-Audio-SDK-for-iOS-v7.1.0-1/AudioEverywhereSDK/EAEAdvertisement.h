//
//  EAEdvertisement.h
//  AudioEverywhereSDK
//
//  Created by Miguel Hernandez on 8/13/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEAdvertisement : NSObject

@property (strong, nonatomic) NSString *type;
@property (strong, nonatomic) NSString *url;
@property (strong, nonatomic) NSNumber *skip;
@property (strong, nonatomic) NSNumber* skipEnabled;

- (id) initDemoAdvertisementFromResource: (NSString *) resourceName;

@end
