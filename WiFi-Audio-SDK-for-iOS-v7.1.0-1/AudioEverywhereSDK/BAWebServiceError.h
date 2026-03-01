//
//  BAWebServiceError.h
//  Basil
//
//  Created by Paula Chavarría on 3/10/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

typedef enum {
    BAWebServiceErrorTypeClient,
    BAWebServiceErrorTypeServer,
    BAWebServiceErrorTypeInternal
} BAWebServiceErrorType;

@interface BAWebServiceError : NSObject

@property (nonatomic) long statusCode;
@property (nonatomic) BAWebServiceErrorType type;
@property (nonatomic, strong) NSURL *failedRequestURL;
@property (nonatomic, strong) NSString *detail;

@end
