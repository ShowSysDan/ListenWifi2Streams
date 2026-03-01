//
//  EAEAudioChannel.h
//  AudioEverywhere
//
//  Created by Paula Chavarría on 4/7/14.
//  Copyright (c) 2014 Exxothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfile.h"
#import "EAEDebugInformation.h"

typedef enum : NSUInteger {
    ChannelStateReady,
    ChannelStatePlaying,
    ChannelStateStopped,
    ChannelStateIssue,
    ChannelStateLoading
} EAEAudioChannelState;

@interface EAEAudioChannel : NSObject

@property (strong, nonatomic) NSString *ipAddress;
@property (strong, nonatomic, readonly) NSString *exxtractorUrl;
@property (strong, nonatomic) NSString *tag;
@property (strong, nonatomic) NSString *title;
@property (strong, nonatomic) NSString *detail;
@property (strong, nonatomic) NSString *subtitle;
@property (nonatomic) EAEAudioChannelState state;
@property (strong, nonatomic) NSString *exxtractorUniqueIdentifier;
@property (strong, nonatomic) NSURL *smallImageUrl;
@property (strong, nonatomic) NSURL *largeImageUrl;
@property (strong, nonatomic) UIColor *backgroundColor;
@property (strong, nonatomic) NSString *uniqueIdentifier;
@property (strong, nonatomic) NSString *rawBackgroundColor;
@property (strong, nonatomic) NSString *port;
@property (nonatomic, assign) BOOL isPA;
@property (nonatomic, assign) BOOL isAvailable;
@property (nonatomic, assign) BOOL isPrivate;
@property (strong, nonatomic) NSString *passphrase;
@property (nonatomic, assign) int32_t apiVersion;
@property (nonatomic, assign) int32_t gain;
@property (nonatomic, assign) BOOL isSHA2Available;
@property (nonatomic, assign) BOOL isHidden;
@property (strong, nonatomic) NSString *leIdAudioOpt;
@property (strong, nonatomic) NSString *leIdServer;
@property (strong, nonatomic) NSArray *listOfLanguages;
@property (nonatomic) EAEDebugInformation *debugInfo;
@property (nonatomic) NSString *jitter;
@property (nonatomic) int32_t bufferSize;

+ (NSDictionary *) getDemoChannelsFromResource: (NSString *)resourceName;

+ (NSString *)encryptPassphrase: (NSString *)passphrase
                isSHA2Available:(BOOL) isSHA2Available;

+ (NSDictionary *) getProfileChannels:(EAEProfile *) profile
                   activeAudioChannel: (EAEAudioChannel *) activeAudioChannel
                     preferedLanguage: (NSString* ) preferedLanguage;

+ (NSArray *) getProfileLanguages:(EAEProfile *) profile;
@end
