//
//  EAEProfileAssets.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 7/12/22.
//  Copyright © 2022 Listen Technologies. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "EAEProfileTheme.h"
#import "EAEWelcomeAd.h"
#import "EAEProfileDocuments.h"
#import "EAEProfileBanners.h"

@interface EAEProfileAssets : NSObject
@property (strong, nonatomic) EAEProfileTheme *theme;
@property (strong, nonatomic) EAEWelcomeAd *welcome_ad;
@property (strong, nonatomic) NSArray *documents;
@property (strong, nonatomic) NSArray *banners;
@property (strong, nonatomic) NSArray *offers;
@end
