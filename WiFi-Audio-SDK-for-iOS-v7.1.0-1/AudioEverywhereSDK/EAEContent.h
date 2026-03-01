//
//  EAEContent.h
//  AudioEverywhere
//
//  Created by Paula Chavarría on 4/7/14.
//  Copyright (c) 2014 Exxothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@class EAESchedule;

enum {
    EAEContentTypeImage = 1,
    EAEContentTypeText = 2,
    EAEContentTypeOffer = 3
};
typedef NSUInteger EAEContentType;

@interface EAEContent:NSObject

@property (strong, nonatomic) NSString *rawBackgroundColor;
@property (strong, nonatomic) NSString *textDescription;
@property (strong, nonatomic) NSString *uniqueIdentifier;
@property (strong, nonatomic) NSURL *featuredImageUrl;
@property (strong, nonatomic) NSURL *dialogImageUrl;
@property (strong, nonatomic) NSURL *thumbnailImageUrl;
@property (strong, nonatomic) NSString *moreInfoUrl;
@property (strong, nonatomic) NSString *title;
@property (strong, nonatomic) NSString *rawType;
@property (strong, nonatomic) EAESchedule *schedule;
@property (strong, nonatomic, readonly) UIColor *backgroundColor;
@property (nonatomic, assign, readonly) EAEContentType type;


+ (NSArray*) getDemoBannersFromResource:(NSString *) resourceName;

+ (NSArray*) getDemoOffersFromResource:(NSString *) resourceName;
+ (NSArray *) getDefaultBannersFromResource:(NSString *) resourceName;
@end
