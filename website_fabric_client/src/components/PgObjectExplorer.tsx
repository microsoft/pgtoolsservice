import { useDispatch } from "react-redux";
import { ObjectExplorerComponent } from "@trident/relational-db-ux/lib/object-explorer";
import {
    BranchNode,
    LoadState,
    openArtifact,
    TreeNode,
} from "@trident/relational-db-ux/lib/sharedStore";
import { useEffect } from "react";
import store, { getObjectExplorerFlatNodeByPath } from "../state/store";
import { getMenuItems } from "../utils/menuItems";
import { ContextMenuItem } from "./ContextMenuItem";

interface Props {
    artifactId: string;
}

const PgObjectExplorer = ({ artifactId }: Props) => {
    const dispatch = useDispatch();

    useEffect(() => {
        // "Artifact" is a top-level concept in Fabric, in our case we expect to
        // only have one, but it must be "opened" initially
        if (artifactId) {
            dispatch(
                openArtifact({
                    artifactPath: artifactId,
                }),
            );
        }
    }, [artifactId, dispatch]);

    return (
        <ObjectExplorerComponent
            getContextMenuOptions={(node) =>
                constructContextMenuOptions(node, artifactId)
            }
        />
    );
};

function constructContextMenuOptions(
    nodePath: string,
    artifactId: string,
): React.ReactNode | undefined {
    const node = getObjectExplorerFlatNodeByPath(store.getState(), nodePath);
    if (!node || node.loadState !== LoadState.Loaded) {
        return;
    }

    return createContextMenu(node, artifactId);
}

const createContextMenu = (node: BranchNode | TreeNode, artifactId: string) => {
    const menuItemDefinitions = getMenuItems(node, artifactId);
    if (menuItemDefinitions && menuItemDefinitions.length > 0) {
        const menuItems = menuItemDefinitions.map((menuItem) => {
            return (
                <ContextMenuItem
                    key={menuItem.label}
                    menuItem={menuItem}
                    onClick={() => {
                        menuItem.onClick();
                    }}
                />
            );
        });
        return <>{menuItems}</>;
    }
};

export default PgObjectExplorer;
