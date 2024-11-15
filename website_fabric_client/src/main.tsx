import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import i18next from "i18next";
import { getTranslations } from "@trident/relational-db-ux/lib/localization";
import { commonIcons } from "@trident/relational-db-ux/lib/icons";
import { initializeIcons } from "@fluentui/react/lib/Icons";
import { registerIcons } from "@fluentui/react/lib/Styling";

import App from "./App.tsx";
import "./index.css";

await initializeLocalization("en");
initializeIcons();
registerIcons({ icons: commonIcons });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

async function initializeLocalization(language: string): Promise<void> {
  const packageTranslation = getTranslations(language);

  await i18next.init({
    returnNull: false,
    lng: language,
    postProcess: [],
    resources: {
      [language]: {
        translation: packageTranslation,
      },
    },
  });
}
