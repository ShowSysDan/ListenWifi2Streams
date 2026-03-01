//
//  EAEProfileOffer.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 15/2/22.
//  Copyright © 2022 Listen Technologies Corporation. All rights reserved.
//

#import <Foundation/Foundation.h>

@class EAESchedule;

@interface EAEProfileOffer : NSObject
@property (strong, nonatomic) NSString *rawBackgroundColor;
@property (strong, nonatomic) NSString *textDescription;
@property (strong, nonatomic) NSString *uniqueIdentifier;
@property (strong, nonatomic) NSString *featuredImageUrl;
@property (strong, nonatomic) NSString *dialogImageUrl;
@property (strong, nonatomic) NSString *thumbnailImageUrl;
@property (strong, nonatomic) NSString *moreInfoUrl;
@property (strong, nonatomic) NSString *title;
@property (strong, nonatomic) NSString *rawType;
@property (strong, nonatomic) EAESchedule *schedule;
@end
