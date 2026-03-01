//
//  EAEReceiverProfileAudioOp.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>


@interface EAEReceiverProfileAudioOp : NSObject
@property (strong, nonatomic) NSString *leid;
@property (strong, nonatomic) NSString *name;
@property (assign, nonatomic) BOOL hidden;
@property (strong, nonatomic) NSString *passphrase;
@property (strong, nonatomic) NSArray *sources;
@end
