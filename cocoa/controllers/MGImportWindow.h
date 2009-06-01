#import <Cocoa/Cocoa.h>
#import "PSMTabBarControl.h"
#import "MGGUIController.h"
#import "MGDocument.h"
#import "MGImportTable.h"
#import "MGImportTableOneSided.h"
#import "PyImportWindow.h"

@interface MGImportWindow : MGGUIController
{
    IBOutlet NSWindow *window;
    IBOutlet PSMTabBarControl *tabBar;
    IBOutlet NSTabView *tabView;
    IBOutlet NSView *mainView;
    IBOutlet NSPopUpButton *targetAccountsPopup;
    IBOutlet NSView *importTablePlaceholder;
    IBOutlet NSPopUpButton *switchDateFieldsPopup;
    IBOutlet NSMenuItem *switchDayMonthMenuItem;
    IBOutlet NSMenuItem *switchMonthYearMenuItem;
    IBOutlet NSMenuItem *switchDayYearMenuItem;
    IBOutlet NSMenuItem *switchDescriptionPayeeMenuItem;
    IBOutlet NSButton *applySwapToAllCheckbox;
    
    MGImportTable *importTable;
    MGImportTableOneSided *importTableOneSided;
    id visibleTable;
    int tabToRemoveIndex;
}
- (id)initWithDocument:(MGDocument *)aDocument;

- (PyImportWindow *)py;
- (void)updateVisibleTable;
/* Actions */
- (IBAction)changeTargetAccount:(id)sender;
- (IBAction)importSelectedPane:(id)sender;
- (IBAction)switchDateFields:(id)sender;

/* Python callbacks */
- (void)close;
- (void)closeSelectedTab;
- (void)refresh;
- (void)show;
- (void)updateSelectedPane;
@end