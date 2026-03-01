//
//  EAEProfileTheme.h
//  ListenEverywhere
//
//  Created by Raul Gomez on 4/6/21.
//  Copyright (c) 2021 Listen Technologies Inc. All rights reserved.
//
#import <Foundation/Foundation.h>

@interface EAEProfileTheme : NSObject

@property (strong, nonatomic) NSString *primaryColor;
@property (strong, nonatomic) NSString *secondaryColor;
@property (assign, nonatomic) BOOL  channel_info_enabled;
@property (strong, nonatomic) NSString *title;
@end
