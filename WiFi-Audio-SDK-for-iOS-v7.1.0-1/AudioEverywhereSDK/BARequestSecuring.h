//
//  BARequestSecuring.h
//  Basil
//
//  Created by Paula Chavarría on 1/6/15.
//  Copyright (c) 2015 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BARequestSecuring.h"

@protocol BARequestSecuring <NSObject>

- (NSMutableURLRequest *) secureRequest: (NSMutableURLRequest *) request;

@end
