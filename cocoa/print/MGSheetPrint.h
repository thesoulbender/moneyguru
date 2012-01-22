/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "MGOutlinePrint.h"
#import "MGDoubleView.h"

@interface MGSheetPrint : MGOutlinePrint
{
    NSView *graphView;
    MGDoubleView *pieViews;
    NSInteger piePage;
    NSInteger graphPage;
}
- (id)initWithPyParent:(PyGUIObject *)pyParent outlineView:(NSOutlineView *)aOutlineView 
    graphView:(NSView *)aGraphView pieViews:(MGDoubleView *)aPieViews;
@end