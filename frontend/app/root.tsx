import type { LinksFunction, MetaFunction } from "@remix-run/node";
import {
    Links,
    LiveReload,
    Meta,
    Outlet,
    Scripts,
    ScrollRestoration,
} from "@remix-run/react";
import { ConfigProvider } from "antd";
import { AppLayout } from "~/components/AppLayout";

import styles from "~/styles/global.css";

export const links: LinksFunction = () => [
    { rel: "stylesheet", href: styles },
];

export const meta: MetaFunction = () => [
    { charset: "utf-8" },
    { title: "Reserving App" },
    { name: "viewport", content: "width=device-width,initial-scale=1" },
];

export default function App() {
    return (
        <html lang="en">
            <head>
                <Meta />
                <Links />
            </head>
            <body>
                <ConfigProvider>
                    <AppLayout>
                        <Outlet />
                    </AppLayout>
                </ConfigProvider>
                <ScrollRestoration />
                <Scripts />
                <LiveReload />
            </body>
        </html>
    );
}
