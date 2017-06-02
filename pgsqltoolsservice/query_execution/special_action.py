# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import IntFlag
import math

class ActionFlags(IntFlag):
    NOFLAGS = 0
    EXPECT_YUKON_XML_SHOW_PLAN = 1

class SpecialAction(object):

    def __init__(self):
        self.flags = ActionFlags.NOFLAGS

    @property
    def NoFlags(self):
        return self.flags == ActionFlags.NOFLAGS

    @NoFlags.setter
    def NoFlags(self):
        self.flags = ActionFlags.NOFLAGS

    @property
    def ExpectYukonXmlShowPlan(self):
        #Return whether the EXPECT_YUKONG_XML_SHOW_PLAN flag bit is set
        return self.flags & (1 << math.floor(ActionFlags.EXPECT_YUKON_XML_SHOW_PLAN / 2) ) == ActionFlags.EXPECT_YUKON_XML_SHOW_PLAN

    @ExpectYukonXmlShowPlan.setter
    def ExpectYukonXmlShowPlan(self, value):
        if value:
            # OR flags with value to apply
            self.flags |= ActionFlags.EXPECT_YUKON_XML_SHOW_PLAN
        else:
            # AND flags with the inverse of the value we want to remove
           self.flags &= ~ActionFlags.EXPECT_YUKON_XML_SHOW_PLAN

    def CombineSpecialAction(self, action):
        self.flags |= action.flags

    