//
//  EAEProfileMenu.h
//  AudioEverywhereSDK
//
//  Created by Elena Delgado on 7/4/22.
//  Copyright © 2022  Listen Technologies Corporation. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfileMenu.h"
#import "EAEProfileMenuOpt.h"

@interface EAEProfileMenu  : NSObject
@property (strong, nonatomic) NSMutableArray<EAEProfileMenuOpt*> * profileMenu;
@end
