/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "PyTable.h"

@interface PyImportTable : PyTable {}
- (BOOL)canBindRow:(NSInteger)source to:(NSInteger)dest;
- (void)bindRow:(NSInteger)source to:(NSInteger)dest;
- (void)unbindRow:(NSInteger)row;
- (BOOL)isTwoSided;
- (void)toggleImportStatus;
@end