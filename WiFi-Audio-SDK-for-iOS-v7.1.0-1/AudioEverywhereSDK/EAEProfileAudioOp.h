//
//  EAEProfileAudioOp.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 5/10/21.
//  Copyright © 2021 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfileAudioOpSourceMobileApp.h"

@interface EAEProfileAudioOp : NSObject

@property (strong, nonatomic) NSString *leid;
@property (strong, nonatomic) NSString *name;
@property (assign, nonatomic) BOOL hidden;
@property (strong, nonatomic) NSString *passphrase;
@property (retain, nonatomic) NSArray *sources;
@property (strong, nonatomic) EAEProfileAudioOpSourceMobileApp *mobile_app;
@end

