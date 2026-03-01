//
//  BALogger.h
//  Basil
//
//  Created by Paula Chavarría on 10/30/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#ifndef Basil_BALogger_h
#define Basil_BALogger_h

#import "DDLog.h"

// Defines the component flags
// The first 5 bits are being used by the standard levels (0 - 4)

// Defines the requests flag
#define LOG_FLAG_BA_REST_REQUEST    (1 << 15)
#define DDLogBARestRequest(frmt, ...) \
do { \
NSString *formatWithTag = [@"[BASIL HTTP REQUEST] " stringByAppendingString: (frmt)]; \
ASYNC_LOG_OBJC_MAYBE(ddLogLevel, LOG_FLAG_BA_REST_REQUEST,  0,  formatWithTag, ##__VA_ARGS__); \
} while (0)

// Defines the requests flag
#define LOG_FLAG_BA_REST_RESPONSE    (1 << 16)
#define DDLogBARestResponse(frmt, ...) \
do { \
NSString *formatWithTag = [@"[BASIL HTTP RESPONSE] " stringByAppendingString: (frmt)]; \
ASYNC_LOG_OBJC_MAYBE(ddLogLevel, LOG_FLAG_BA_REST_RESPONSE,  0,  formatWithTag, ##__VA_ARGS__); \
} while (0)

#endif
