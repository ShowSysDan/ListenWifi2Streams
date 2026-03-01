//
//  EAEWelcomeAd.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 1/10/21.
//  Copyright © 2021 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface EAEWelcomeAd : NSObject
@property (strong, nonatomic) NSString *locationName;
@property (strong, nonatomic) NSString *locationLogoUrl;
@property (strong, nonatomic) NSString *locationBackUrl;
@property (strong, nonatomic) NSString *locationTabletBackUrl;
@property (strong, nonatomic) NSString *locationDialogUrl;
@property (strong, nonatomic) NSString *locationTabletDialogUrl;
@property (strong, nonatomic) NSString *adType;
@property (strong, nonatomic) NSString *adSmallImageUrl;
@property (strong, nonatomic) NSString *adLargeImagUrl;
@property (strong, nonatomic) NSString *adVideoUrl;
@property (strong, nonatomic) NSNumber *adSkipTime;
@property (strong, nonatomic) NSNumber *adSkipEnabled;
@property (strong, nonatomic) NSString *exxtractorUniqueIdentifier;
@property (strong, nonatomic) NSString *exxtractorVersion;
@end

