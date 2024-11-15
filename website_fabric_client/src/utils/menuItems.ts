import { t } from "i18next";
import {
    BranchNode,
    LeafNode,
    loadChildNodes,
} from "@trident/relational-db-ux/lib/sharedStore";
import store from "../state/store";

export interface TreeNodeContextMenuItem {
    label: string;
    onClick: () => void;
    disabled?: boolean;
    icon?: string;
    tooltip?: string;
}

const getRefreshNodeMenuItem = (
    nodePath: string,
    disabled?: boolean,
    tooltip?: string,
): TreeNodeContextMenuItem => ({
    onClick: () => store.dispatch(loadChildNodes({ parentPath: nodePath })),
    label: t("Refresh"),
    disabled,
    tooltip,
});

export function getMenuItems(
    node: BranchNode | LeafNode,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    artifactId: string,
): TreeNodeContextMenuItem[] {
    const menuItems: TreeNodeContextMenuItem[] = [];
    const refreshMenuItem = getRefreshNodeMenuItem(node.path);

    menuItems.push(refreshMenuItem);
    return menuItems;
}
