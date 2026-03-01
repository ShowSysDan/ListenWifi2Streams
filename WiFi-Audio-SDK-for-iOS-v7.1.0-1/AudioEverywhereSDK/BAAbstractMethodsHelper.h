//
//  BAAbstractMethodsHelper.h
//  Basil
//
//  Created by Paula Chavarría on 7/29/14.
//  Copyright (c) 2014 Cecropia Solutions. All rights reserved.
//

#ifndef Basil_BAAbstractMethodsHelper_h
#define Basil_BAAbstractMethodsHelper_h

#define mustOverride() @throw [NSException exceptionWithName:NSInvalidArgumentException reason:[NSString stringWithFormat:@"%s must be overridden in a subclass/category", __PRETTY_FUNCTION__] userInfo:nil]

#endif
