//
//  EAEReceiverProfileSetting.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEReceiverProfileSetting : NSObject

@property (strong, nonatomic) NSString* audio_language;
@property (assign, nonatomic) NSInteger auto_off_timeout;
@property (assign, nonatomic) BOOL auto_power;
@property (strong, nonatomic) NSString* brightness;
@property (assign, nonatomic) BOOL jack_sense;
@property (strong, nonatomic) NSString* text_language;
@property (assign, nonatomic) NSInteger volume;


@end
