import React, { useState } from "react";
import { Icon } from "@fluentui/react";
import { MenuItem, Tooltip } from "@fluentui/react-components";
import { TreeNodeContextMenuItem } from "../utils/menuItems";

type ContextMenuItemProps = {
    menuItem: TreeNodeContextMenuItem;
    onClick: () => void;
};
export const ContextMenuItem: React.FC<ContextMenuItemProps> = ({
    menuItem,
    onClick,
}) => {
    const [showToolTip, setToolTip] = useState(false);
    return (
        <Tooltip
            content={menuItem.tooltip ?? ""}
            relationship="description"
            withArrow={true}
            visible={showToolTip && !!menuItem.tooltip}
        >
            <MenuItem
                key={menuItem.label}
                disabled={menuItem.disabled}
                onMouseEnter={() => setToolTip(true)}
                onMouseLeave={() => setToolTip(false)}
                icon={menuItem.icon && <Icon iconName={menuItem.icon} />}
                onClick={onClick}
            >
                {menuItem.label}
            </MenuItem>
        </Tooltip>
    );
};
