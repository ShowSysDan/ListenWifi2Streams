//
//  EAEProfileChannel.h
//  ListenEverywhere
//
//  Created by Raul Gomez on 04/08/21.
//  Copyright (c) 2021 Listen Technologies Inc. All rights reserved.
//
#import <Foundation/Foundation.h>

@interface EAEProfileChannel : NSObject
@property (strong, nonatomic) NSString *name;
@property (nonatomic, assign) BOOL isPa;
@property (strong, nonatomic) NSString *detail;
@property (nonatomic) long number;
@property (strong, nonatomic) NSURL *smallImageUrl;
@property (strong, nonatomic) NSURL *largeImageUrl;
@property (nonatomic, assign) int32_t gain;
@property (nonatomic, assign) BOOL isPrivate;
@property (strong, nonatomic) NSString *passphrase;
@property (strong, nonatomic) NSString *port;
@property (strong, nonatomic) NSString *ipAddress;
@property (strong, nonatomic) NSString *backgroundColor;
@property (nonatomic, assign) BOOL isAvailable;
@property (nonatomic, assign) int32_t apiVersion;
@property (strong, nonatomic, readonly) NSString *uniqueIdentifier;
@end
