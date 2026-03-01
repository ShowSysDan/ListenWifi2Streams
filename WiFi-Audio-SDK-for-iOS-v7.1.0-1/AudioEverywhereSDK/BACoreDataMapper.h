//
//  BACoreDataBuilder.h
//  Basil
//
//  Created by Paula Chavarría on 11/10/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <CoreData/CoreData.h>

@interface BACoreDataMapper : NSObject

- (id)mapToClass: (Class) aClass fromEntity: (NSManagedObject *) entityObject;
- (id)mapToEntity: (NSManagedObject *) entityObject fromObject: (id) fromObject;

@end
