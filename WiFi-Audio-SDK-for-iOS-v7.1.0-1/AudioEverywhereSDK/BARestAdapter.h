//
//  BARestAdapter.h
//  Basil
//
//  Created by Paula Chavarría on 3/12/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "BAWebServiceResponse.h"
#import "BAObjectMapConfiguring.h"
#import "BARequestSecuring.h"

@interface BARestAdapter : NSObject

@property (strong, nonatomic) NSString *baseURLString;
@property (strong, nonatomic) id<BAObjectMapConfiguring> objectMapConfigurator;
@property (strong, nonatomic) NSMutableDictionary *defaultHeaders;
@property (nonatomic) Class serverErrorClass;
@property (nonatomic) Class clientErrorClass;
@property (nonatomic) int requestTimeout;
@property (nonatomic, strong) id<BARequestSecuring> requestSecurity;

- (id)initWithObjectMappingConfigurator:(id<BAObjectMapConfiguring>)objectMapConfigurator
                          baseURLString:(NSString *)baseURLString
                         defaultHeaders:(NSDictionary *) defaultHeaders;

- (id)initWithObjectMappingConfigurator:(id<BAObjectMapConfiguring>)objectMapConfigurator
                          baseURLString:(NSString *)baseURLString
                         defaultHeaders:(NSDictionary *) defaultHeaders
                       clientErrorClass:(Class) clientErrorClass
                       serverErrorClass:(Class) serverErrorClass;

- (void) addDefaultHeader:(NSString *)header value:(NSString *)value;

- (void)   getObjectsAtPath:(NSString *)path
                    headers:(NSDictionary *)headers
                 parameters:(NSDictionary *)parameters
                    keyPath:(NSString *) keyPath
                    success:(BAWebServiceSuccessResponse)success
                    failure:(BAWebServiceFailureResponse)failure
        responseObjectClass:(Class)responseObjectClass
   requiresSecureConnection: (bool) requiresSecureConnection;

- (void)         postObject:(id)object
                     atPath:(NSString *)path
                    headers:(NSDictionary *)headers
                 parameters:(NSDictionary *)parameters
                    keyPath:(NSString *) keyPath
                    success:(BAWebServiceSuccessResponse)success
                    failure:(BAWebServiceFailureResponse)failure
        responseObjectClass:(Class)responseObjectClass
        requiresSecureConnection: (bool) requiresSecureConnection;


- (void)          putObject:(id)object
                     atPath:(NSString *)path
                    headers:(NSDictionary *)headers
                 parameters:(NSDictionary *)parameters
                    keyPath:(NSString *) keyPath
                    success:(BAWebServiceSuccessResponse)success
                    failure:(BAWebServiceFailureResponse)failure
        responseObjectClass:(Class)responseObjectClass
   requiresSecureConnection: (bool) requiresSecureConnection;


- (void)       deleteObject:(id)object
                     atPath:(NSString *)path
                    headers:(NSDictionary *)headers
                 parameters:(NSDictionary *)parameters
                    keyPath:(NSString *) keyPath
                    success:(BAWebServiceSuccessResponse)success
                    failure:(BAWebServiceFailureResponse)failure
        responseObjectClass:(Class)responseObjectClass
   requiresSecureConnection: (bool) requiresSecureConnection;


@end
