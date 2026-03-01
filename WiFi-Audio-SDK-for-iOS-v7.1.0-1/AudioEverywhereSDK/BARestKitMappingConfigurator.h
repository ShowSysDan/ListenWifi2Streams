//
//  BARestKitMappingConfigurator.h
//  Basil
//
//  Created by Paula Chavarría on 3/12/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BAObjectMapConfiguring.h"

@class RKRequestDescriptor;
@class RKResponseDescriptor;

@protocol BARestKitMappingConfiguratorDelegate

- (void)updateRequestDescriptor:(RKRequestDescriptor *)requestDescriptor;
- (void)updateResponseDescriptor:(RKResponseDescriptor *)responseDescriptor;

@end

@interface BARestKitMappingConfigurator : NSObject<BAObjectMapConfiguring>

@property (strong, nonatomic) id<BARestKitMappingConfiguratorDelegate> delegate;
@property (strong, nonatomic) NSMutableDictionary *registeredMappings;

@end
