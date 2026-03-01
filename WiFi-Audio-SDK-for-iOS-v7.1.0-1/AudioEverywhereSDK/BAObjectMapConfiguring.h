//
//  BAObjectMapConfiguring.h
//  Basil
//
//  Created by Paula Chavarría on 3/12/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BAWebService.h"

typedef enum : int {
    BAMappingTypeRequest = 0,
    BAMappingTypeResponse = 1
} BAMappingType;

@protocol BAObjectMapConfiguring <NSObject>

@property (strong, nonatomic) NSMutableDictionary *registeredMappings;

/*!
   Configures the mapping for the REST adapter
 
   @param path                The request endpoint
   @param method              The HTTP request method
   @param responseEntityClass The class of the response entity
   @param requestEntityClass  The class of the request entity
   @param keyPath             The key path to match against the deserialized response body. 
                              If nil, the response descriptor matches the entire response body.
 */
- (void)configureMappingWithPath:(NSString *)path
                      httpMethod:(BAWebServiceHttpMethod)method
             responseEntityClass:(Class)responseEntityClass
              requestEntityClass:(Class)requestEntityClass
                         keyPath:(NSString *)keyPath;

/*!
 Configures the mapping the server and the client error mapping
 
 @param serverErrorClass The class of the server error response entity
 @param clientErrorClass The class of the client error response entity
 */
- (void)configureServerErrorMapping:(Class) serverErrorClass clientErrorClass: (Class) clientErrorClass;

@end
