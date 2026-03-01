//
//  UIBarButtonItem+CustomPaddingSetter.h
//  StreamCatcher
//
//  Created by Eduardo Gamboa on 12/13/13.
//  Copyright (c) 2013 Cecropia Solutions. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface UIBarButtonItem (CustomPaddingSetter)


+ (UIBarButtonItem*)barItemWithImage:(UIImage*)image highlightedImage:(UIImage*)highlightedImage xOffset:(NSInteger)xOffset target:(id)target action:(SEL)action;

+ (UIBarButtonItem*)barItemWithTitle:(NSString*)title xOffset:(NSInteger)xOffset target:(id)target action:(SEL)action;


@end
