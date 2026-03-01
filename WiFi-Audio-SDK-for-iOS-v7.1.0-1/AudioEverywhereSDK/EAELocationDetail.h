//
//  EAEVenueDetail.h
//  AudioEverywhereSDK
//
//  Created by Miguel Hernandez on 8/13/14.
//  Copyright (c) 2014 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>


@interface EAELocationDetail : NSObject

@property (strong, nonatomic) NSString *name;
@property (strong, nonatomic) NSURL *logoImageUrl;
@property (strong, nonatomic) NSString *uniqueIdentifier;
@property (strong, nonatomic) NSURL *featuredContentImageUrl;
@property (strong, nonatomic) NSURL *detailContentImageUrl;
@property (strong, nonatomic) NSURL *appStoreUrl;
@property (strong, nonatomic) NSString *partnerUniqueIdentifier;
@property (strong, nonatomic) NSString *exxtractorUniqueIdentifier;
@property (strong, nonatomic) NSString *exxtractorVersion;

- (id) initDemoLocationDetailFromResource: (NSString*) resourceName;

@end
