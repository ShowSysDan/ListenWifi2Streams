//
//  WebService+RestKit.h
//  Basil
//
//  Created by Paula Chavarría on 3/13/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import "BAWebService.h"
#import "Restkit/ObjectMapping/RKHTTPUtilities.h"

@interface BAWebService (RestKit)

+ (RKRequestMethod)convertToRKRequestMethod:(BAWebServiceHttpMethod)method;
+ (void) enableLogginTracingForComponent:(NSString*)component;

@end
