//
//  EAEReceiverProfileAudioOpSource.h
//  ListenWIFISDK
//
//  Created by Elena Delgado on 8/5/23.
//  Copyright © 2023 Listen Technologies In. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEReceiverProfileAudioOpSourceResource.h"

@interface EAEReceiverProfileAudioOpSource : NSObject

@property (strong, nonatomic) NSString *tag;
@property (strong, nonatomic) NSString *type;
@property (strong, nonatomic) EAEReceiverProfileAudioOpSourceResource * resource;

@end
