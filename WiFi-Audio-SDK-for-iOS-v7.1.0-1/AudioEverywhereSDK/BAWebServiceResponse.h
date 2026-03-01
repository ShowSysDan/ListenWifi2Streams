//
//  BAWebServiceResponse.h
//  Basil
//
//  Created by Paula Chavarría on 3/10/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#ifndef Basil_BAWebServiceResponse_h
#define Basil_BAWebServiceResponse_h

#import "BAWebServiceError.h"

typedef void (^BAWebServiceSuccessResponse)(NSArray *result);
typedef void (^BAWebServiceFailureResponse)(BAWebServiceError *error);

#endif
