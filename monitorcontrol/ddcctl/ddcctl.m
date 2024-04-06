//  Copyright Joey Korkames 2016 http://github.com/kfix
//  Licensed under GPLv3, full text at http://www.gnu.org/licenses/gpl-3.0.txt

#import <Foundation/Foundation.h>
#import <AppKit/NSScreen.h>
#import "DDC.h"

extern io_service_t CGDisplayIOServicePort(CGDirectDisplayID display) __attribute__((weak_import));

NSString *getDisplayDeviceLocation(CGDirectDisplayID cdisplay)
{
    // FIXME: scraping prefs files is vulnerable to use of stale data?
    // TODO: try shelling `system_profiler SPDisplaysDataType -xml` to get "_spdisplays_displayPath" keys
    //    this seems to use private routines in:
    //      /System/Library/SystemProfiler/SPDisplaysReporter.spreporter/Contents/MacOS/SPDisplaysReporter

    // get the WindowServer's table of DisplayIds -> IODisplays
    NSString *wsPrefs = @"/Library/Preferences/com.apple.windowserver.plist";
    NSDictionary *wsDict = [NSDictionary dictionaryWithContentsOfFile:wsPrefs];
    if (!wsDict) return NULL;

    NSArray *wsDisplaySets = [wsDict valueForKey:@"DisplayAnyUserSets"];
    if (!wsDisplaySets) return NULL;

    // $ PlistBuddy -c "Print DisplayAnyUserSets:0:0:IODisplayLocation" -c "Print DisplayAnyUserSets:0:0:DisplayID" /Library/Preferences/com.apple.windowserver.plist
    // > IOService:/AppleACPIPlatformExpert/PCI0@0/AppleACPIPCI/PEG0@1/IOPP/GFX0@0/ATY,Longavi@0/AMDFramebufferVIB
    // > 69733382
    for (NSArray *displaySet in wsDisplaySets) {
        for (NSDictionary *display in displaySet) {
            if ([[display valueForKey:@"DisplayID"] integerValue] == cdisplay) {
                return [display valueForKey:@"IODisplayLocation"]; // kIODisplayLocationKey
            }
        }
    }

    return NULL;
}

/* Get current value for control from display */
uint getControl(CGDirectDisplayID cdisplay, uint control_id)
{
    struct DDCReadCommand command;
    command.control_id = control_id;
    command.max_value = 0;
    command.current_value = 0;

    DDCRead(cdisplay, &command);
    return command.current_value;
}

/* Set new value for control from display */
void setControl(io_service_t framebuffer, uint control_id, uint new_value)
{
    struct DDCWriteCommand command;
    command.control_id = control_id;
    command.new_value = new_value;

    DDCWrite(framebuffer, &command);
}

/* Get current value to Set relative value for control from display */
void getSetControl(io_service_t framebuffer, uint control_id, NSString *new_value, NSString *operator)
{
    struct DDCReadCommand command;
    command.control_id = control_id;
    command.max_value = 0;
    command.current_value = 0;

    // read
    DDCRead(framebuffer, &command);

    // calculate
    NSString *formula = [NSString stringWithFormat:@"%u %@ %@", command.current_value, operator, new_value];
    NSExpression *exp = [NSExpression expressionWithFormat:formula];
    NSNumber *set_value = [exp expressionValueWithObject:nil context:nil];

    // validate and write
    int clamped_value = MIN(MAX(set_value.intValue, 0), command.max_value);
    setControl(framebuffer, control_id, (uint) clamped_value);
}

NSMutableArray *getDisplayIds(void)
{
    NSMutableArray *_displayIDs = [NSMutableArray arrayWithCapacity:30];

    for (NSScreen *screen in NSScreen.screens) {
        NSDictionary *description = [screen deviceDescription];
        if ([description objectForKey:@"NSDeviceIsScreen"]) {
            CGDirectDisplayID screenNumber = [[description objectForKey:@"NSScreenNumber"] unsignedIntValue];
            if (CGDisplayIsBuiltin(screenNumber)) continue; // ignore MacBook screens because the lid can be closed and they don't use DDC.
            [_displayIDs addObject:[NSNumber numberWithUnsignedInteger: screenNumber]];
        }
    }

    return _displayIDs;
}

io_service_t getFrameBuffer(NSUInteger displayId)
{
    NSMutableArray *_displayIDs = getDisplayIds();

    if (0 >= displayId || displayId > [_displayIDs count]) {
        // no display id given, nothing left to do!
        return 0;
    }

    CGDirectDisplayID cdisplay = ((NSNumber *)_displayIDs[displayId - 1]).unsignedIntegerValue;

    // find & grab the IOFramebuffer for the display, the IOFB is where DDC/I2C commands are sent
    io_service_t framebuffer = 0;
    NSString *devLoc = getDisplayDeviceLocation(cdisplay);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    if (CGDisplayIOServicePort != NULL) {
        // legacy API call to get the IOFB's service port, was deprecated after macOS 10.9:
        //     https://developer.apple.com/library/mac/documentation/GraphicsImaging/Reference/Quartz_Services_Ref/index.html#//apple_ref/c/func/CGDisplayIOServicePort
        framebuffer = CGDisplayIOServicePort(cdisplay);
#pragma clang diagnostic pop
    }

    if (!framebuffer && devLoc) {
        // a devLoc is required because, without that IOReg path, this func is prone to always match the 1st device of a monitor-pair (#17)
        framebuffer = IOFramebufferPortFromCGDisplayID(cdisplay, (__bridge CFStringRef)devLoc);
    }

    if (!framebuffer) {
        return 0;
    }

    struct EDID edid = {};
    if (!EDIDTest(framebuffer, &edid)) {
        IOObjectRelease(framebuffer);
        return 0;
    }

	// Be sure to call IOObjectRelease on this when you're done with it!
    return framebuffer;
}

