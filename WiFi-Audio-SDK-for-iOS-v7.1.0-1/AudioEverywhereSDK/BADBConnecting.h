//
//  BADBConnecting.h
//  Basil
//
//  Created by Paula Chavarría on 10/23/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

@protocol BADBConnecting <NSObject>

/*!
 Method which opens the connection with the DB
 
 @param error An error indicating if there was a problem opening the connection
 */
- (void) openWithError:(NSError **)error;

/*!
 Method which creates the rows for a given collection of models
 
 @param collection The collection of models that will be created
 @param entityName The name of the entity that matches the collection models
 @param error      An error indicating if there was a problem with the operation
 */
- (void) createCollection: (NSArray *) collection entityName:(NSString *) entityName error: (NSError **) error;

/*!
 Method which fetches a collection based on a given predicate and a sort descriptor collection
 
 @param predicate      The predicate used in the fetch operation
 @param sortDescriptors The sort descriptors collection used in the fetch operation
 @param entityName     The name of the entity that matches the collection models
 @param modelClass     The name of the class in which the result collection should be returned
 @param error          An error indicating if there was a problem with the operation
 
 @return The collection of rows
 */
- (NSArray *) findWithPredicate: (NSPredicate *) predicate
                 sortDescriptor: (NSArray *) sortDescriptors
                     entityName: (NSString *) entityName
                     modelClass: (Class) modelClass
                          error: (NSError **) error;

/*!
 Method which updates the rows for a given collection of models
 
 @param collection The collection of models that will be updated
 @param predicate  The predicate used to identify the existing rows
 @param entityName The name of the entity that matches the collection models
 @param error      An error indicating if there was a problem with the operation
 */
- (void) updateCollection: (NSArray *) collection
                predicate: (NSPredicate *) predicate
               entityName:(NSString *) entityName
                    error: (NSError **) error;

@end

