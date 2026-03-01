//
//  BAWebService.h
//  Basil
//
//  Created by Paula Chavarría on 3/10/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

@class BARestAdapter;

typedef enum : int {
    BAWebServiceHttpMethodGET = 0,
    BAWebServiceHttpMethodPOST = 1,
    BAWebServiceHttpMethodPUT = 2,
    BAWebServiceHttpMethodDELETE = 3
} BAWebServiceHttpMethod;

@interface BAWebService : NSObject

@property (strong, nonatomic) BARestAdapter *restAdapter;

- (id)initWithRestAdapter:(BARestAdapter *)restAdapter;
+ (NSString *) httpMethodToString: (BAWebServiceHttpMethod) method;

@end
