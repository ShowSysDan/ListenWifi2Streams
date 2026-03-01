//
//  EAEReceiverVenueConfFile.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 3/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEReceiverVenueConfFile : NSObject

@property (strong, nonatomic) NSString* leid;
@property (strong, nonatomic) NSString* name;
@property (assign, nonatomic) NSString* passphrase;
@property (assign, nonatomic) BOOL passphrase_required;
@property (assign, nonatomic) NSInteger version;

@end
