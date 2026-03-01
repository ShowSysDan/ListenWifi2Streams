//
//  BARestKitAdapter.h
//  Basil
//
//  Created by Paula Chavarría on 3/12/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BARestAdapter.h"
#import "BARestKitMappingConfigurator.h"

@interface BARestKitAdapter : BARestAdapter<BARestKitMappingConfiguratorDelegate>

@end
