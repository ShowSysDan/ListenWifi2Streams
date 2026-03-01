//
//  BANetworkHelper.h
//  Basil
//
//  Created by Paula Chavarría on 3/26/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#include <ifaddrs.h>
#include <arpa/inet.h>

@interface BANetworkHelper : NSObject

+ (NSString *)ipAddress;

@end
