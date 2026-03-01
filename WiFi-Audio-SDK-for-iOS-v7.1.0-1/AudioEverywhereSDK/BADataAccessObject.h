//
//  BADataAccessObject.h
//  Basil
//
//  Created by Paula Chavarría on 11/12/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BADBConnecting.h"

@interface BADataAccessObject : NSObject

@property (nonatomic, strong) id<BADBConnecting> dbConnection;

- (id) initWithDBConnection: (id<BADBConnecting>) dbConnection;

@end
