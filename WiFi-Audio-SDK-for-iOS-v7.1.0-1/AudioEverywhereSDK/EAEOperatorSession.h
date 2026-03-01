//
//  EAEOperatorSession.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 10/5/23.
//  Copyright © 2023 Listen Technologies Inc. All rights reserved.
//

#import <Foundation/Foundation.h>


@interface EAEOperatorSession : NSObject

@property (strong, nonatomic) NSString* access_token;
@property (strong, nonatomic) NSString* token_type;

@end
