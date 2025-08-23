import type { AppConfig } from "@remix-run/dev";

export default {
    ignoredRouteFiles: ["**/.*"],
    serverModuleFormat: "esm",
    serverDependenciesToBundle: ["antd"],
} satisfies AppConfig;
