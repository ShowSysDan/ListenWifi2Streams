//
//  EAEProfileAudioOpSourceMobileApp.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 5/10/21.
//  Copyright © 2021 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEProfileAudioOpSourceMobileApp : NSObject

@property (strong, nonatomic) NSString *channelId;
@property (strong, nonatomic) NSString *channelName;
@property (assign, nonatomic) BOOL isEnabled;
@property (strong, nonatomic) NSString *imageUrl;
@property (strong, nonatomic) NSString *largeImageUrl;
@property (strong, nonatomic) NSString *channelDescription;
@property (strong, nonatomic) NSString *channelColor;
@property (assign, nonatomic) BOOL isAvailable;
@property (strong, nonatomic) NSString *channelBackgroundColor;
@property (strong, nonatomic) NSString *channelPlayingImageUrl;

@end
