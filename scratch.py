import Foundation
import AppKit
import Quartz
import objc

#######
# get list of displays
#######
error, display_ids_tuple, display_count = Quartz.CGGetOnlineDisplayList(16, None, None)
if error:
    raise OSError(f"Could not get display list. Error: {error}")

print(display_ids_tuple)

#####
# get list of IOregService, for matching displays against later
#####
IOKit = Foundation.NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')
functions = [("")]
io_reg_entry =

#######
# try to get DDC services, and skip displays which error
######
display_ids = []
for d in display_ids_tuple:
    pass