//
//  EAEReceiverProfileServer.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEReceiverProfileServer : NSObject

@property (strong, nonatomic) NSString *serial_number;
@property (strong, nonatomic) NSString *last_known_ip;

@end
