//
//  EAEProfileMenuOpt.h
//  AudioEverywhereSDK
//
//  Created by Elena Delgado on 7/4/22.
//  Copyright © 2022 Listen Technologies Corporation. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEProfileMenuOpt  : NSObject
@property (strong, nonatomic) NSString * leid;
@property (strong, nonatomic) NSString * name;
@property (assign, nonatomic) BOOL passphrase_required;
@property (nonatomic) long version;
@end
