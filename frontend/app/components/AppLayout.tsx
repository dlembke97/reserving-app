import React from "react";
import { Layout, Menu } from "antd";
import { Link, useLocation } from "@remix-run/react";
import {
    DashboardOutlined,
    UploadOutlined,
} from "@ant-design/icons";

const { Header, Sider, Content } = Layout;

interface AppLayoutProps {
    children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
    const location = useLocation();

    const menuItems = [
        {
            key: "/",
            icon: <DashboardOutlined />,
            label: <Link to="/">Dashboard</Link>,
        },
        {
            key: "/triangles/upload",
            icon: <UploadOutlined />,
            label: <Link to="/triangles/upload">Upload Triangle</Link>,
        },
    ];

    const selectedKey = location.pathname === "/triangles/upload" ? "/triangles/upload" : "/";

    return (
        <Layout style={{ minHeight: "100vh" }}>
            <Sider width={250} theme="dark">
                <div style={{
                    height: 64,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "white",
                    fontSize: "18px",
                    fontWeight: "bold"
                }}>
                    Reserving App
                </div>
                <Menu
                    theme="dark"
                    mode="inline"
                    selectedKeys={[selectedKey]}
                    items={menuItems}
                />
            </Sider>
            <Layout>
                <Header style={{
                    background: "#fff",
                    padding: "0 24px",
                    display: "flex",
                    alignItems: "center"
                }}>
                    <h1 style={{ margin: 0, fontSize: "20px" }}>
                        {selectedKey === "/" ? "Dashboard" : "Upload Triangle"}
                    </h1>
                </Header>
                <Content style={{
                    margin: "24px 16px",
                    padding: 24,
                    background: "#fff",
                    borderRadius: "6px",
                    minHeight: "calc(100vh - 112px)"
                }}>
                    {children}
                </Content>
            </Layout>
        </Layout>
    );
}
