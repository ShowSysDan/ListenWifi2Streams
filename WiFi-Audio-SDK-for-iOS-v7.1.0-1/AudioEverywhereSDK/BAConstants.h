//
//  BAConstants.h
//  Basil
//
//  Created by Paula Chavarría on 4/4/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface BAConstants : NSObject

#pragma mark -
#pragma mark Formats

extern NSString *const kBAFormatForStringWithStringPort;
extern NSString *const kBAFormatForStringWithIntegerPort;
extern NSString *const kBAFormatForHexColor;
extern NSString *const kBAFormatForStringWithEllipsis;
extern NSString *const kBAFormatForStringWithInt;

#pragma mark -
#pragma mark General

extern NSString *const kBAEmptyString;
extern NSString *const kBASpaceString;
extern NSString *const kBANumberSign;
extern NSString *const kBAColonString;
extern NSString *const kBACommaString;
extern NSString *const kBAPeriodString;

#pragma mark -
#pragma mark File Extensions

extern NSString *const kBAFileExtensionPlist;
extern NSString *const kBAFileExtensionSqlite;

#pragma mark -
#pragma mark iOS SDK related

extern NSString *const kBAIOSCFBundleVersion;
extern NSString *const kBAIOSCFBundleShortVersionString;
extern NSString *const kBAIOSWifiInterface;
extern NSString *const kBAWifiDisconnected;

#pragma mark -
#pragma mark Error related

extern NSString *const kBAErrorDomain;
extern int const kBAErrorCodeForCoreDataConnectionInvalidStore;
extern int const kBAErrorCodeForCoreDataSaveError;

#pragma mark -
#pragma mark Connection protocols
extern NSString *const kBARestAdapterHTTPPrefix;
extern NSString *const kBARestAdapterHTTPSPrefix;
extern NSString *const kBAVenueServerPort;

@end
