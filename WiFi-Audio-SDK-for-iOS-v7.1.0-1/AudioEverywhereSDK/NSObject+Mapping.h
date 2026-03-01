//
//  NSObject+Mapping.h
//  Basil
//
//  Created by Paula Chavarría on 3/24/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface NSObject (Mapping)

+ (id)objectMappingForPath:(NSString *) path
          forSerialization:(NSNumber *)forSerialization;

@end
