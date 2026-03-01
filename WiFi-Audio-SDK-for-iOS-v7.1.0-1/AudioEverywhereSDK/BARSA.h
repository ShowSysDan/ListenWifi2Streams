//
//  BARSA.h
//  AudioEverywhereManager
//
//  Created by Paula Chavarría on 1/8/15.
//  Copyright (c) 2015 ExXothermic. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface BARSA : NSObject {
    SecKeyRef publicKey;
    SecCertificateRef certificate;
    SecPolicyRef policy;
    SecTrustRef trust;
    size_t maxPlainLen;
}

- (id)initWithPublicKeyPath:(NSString *)publicKeyPath publicKeyLength:(int) publicKeyLength;
- (id)initWithData:(NSData *)keyData publicKeyLength:(int) publicKeyLength;
- (NSData *) encryptWithData:(NSData *)content;
- (NSData *) encryptWithString:(NSString *)content;
- (NSString *) encryptToString:(NSString *)content;

@end
