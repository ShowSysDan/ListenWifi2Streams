//
//  BACoreDataConnection.h
//  Basil
//
//  Created by Paula Chavarría on 10/23/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BADBConnecting.h"

@class NSManagedObjectContext;
@class NSManagedObjectModel;
@class NSPersistentStoreCoordinator;
@class BACoreDataMapper;

@interface BACoreDataConnection : NSObject <BADBConnecting>

- (id) initWithModelName: (NSString *) modelName
          modelExtension: (NSString *) modelExtension
     persistentStoreType: (NSString *) persistentStoreType
          coreDataMapper: (BACoreDataMapper *) coreDataMapper;

@end
