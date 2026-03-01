//
//  EAEProfileDocument.h
//  ListenEverywhereSDK
//
//  Created by Elena Delgado on 10/2/22.
//  Copyright © 2022 Listen Technologies Corporation. All rights reserved.
//

#import <Foundation/Foundation.h>
@interface EAEProfileDocument : NSObject
@property (strong, nonatomic) NSString *documentId;
@property (strong, nonatomic) NSString *url;
@property (strong, nonatomic) NSString *name;
@property (strong, nonatomic) NSString *expirationDate;
@property (strong, nonatomic) NSString *category;

@end
