//
//  EAEProfileAudioOpSource.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 5/10/21.
//  Copyright © 2021 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfileAudioOpSourceResourse.h"


@interface EAEProfileAudioOpSource : NSObject

@property (strong, nonatomic) NSString *tag;
@property (strong, nonatomic) NSString *type;
@property (strong, nonatomic) EAEProfileAudioOpSourceResourse * resource;


@end


