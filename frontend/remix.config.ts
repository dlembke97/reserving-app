import type { AppConfig } from "@remix-run/dev";

export default {
    ignoredRouteFiles: ["**/.*"],
    serverModuleFormat: "esm",
    serverDependenciesToBundle: ["antd"],
    appDirectory: "app",
    serverEntryPoint: "app/entry.server.tsx",
} satisfies AppConfig;
