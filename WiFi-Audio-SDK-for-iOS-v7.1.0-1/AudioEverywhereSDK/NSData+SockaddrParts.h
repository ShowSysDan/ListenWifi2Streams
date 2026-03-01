//
//  NSData+SockaddrParts.h
//  Basil
//
//  Created by Paula Chavarría on 3/7/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface NSData (SockaddrParts)

- (NSString *) address;
- (NSString *) port;

@end
