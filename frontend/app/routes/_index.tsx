import React from "react";
import { Card, Row, Col, Statistic, Typography, Space } from "antd";
import {
    BarChartOutlined,
    FileTextOutlined,
    CalculatorOutlined,
    RiseOutlined
} from "@ant-design/icons";

const { Title, Paragraph } = Typography;

export default function Dashboard() {
    return (
        <div>
            <Title level={2}>Dashboard</Title>
            <Paragraph>
                Welcome to the Reserving App. Upload your loss triangles to analyze reserves using
                Mack Chainladder, Cape Cod, and other actuarial methods.
            </Paragraph>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Total Analyses"
                            value={0}
                            prefix={<CalculatorOutlined />}
                            valueStyle={{ color: "#3f8600" }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Mack Ultimate"
                            value={0}
                            prefix={<RiseOutlined />}
                            valueStyle={{ color: "#1890ff" }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Cape Cod Ultimate"
                            value={0}
                            prefix={<BarChartOutlined />}
                            valueStyle={{ color: "#722ed1" }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Files Processed"
                            value={0}
                            prefix={<FileTextOutlined />}
                            valueStyle={{ color: "#fa8c16" }}
                        />
                    </Card>
                </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col xs={24} lg={12}>
                    <Card title="Recent Activity" size="small">
                        <Paragraph type="secondary">
                            No recent activity. Upload your first triangle to get started.
                        </Paragraph>
                    </Card>
                </Col>
                <Col xs={24} lg={12}>
                    <Card title="Quick Actions" size="small">
                        <Space direction="vertical" style={{ width: "100%" }}>
                            <Paragraph>
                                • Upload a new loss triangle for analysis
                            </Paragraph>
                            <Paragraph>
                                • View historical analysis results
                            </Paragraph>
                            <Paragraph>
                                • Export analysis reports
                            </Paragraph>
                        </Space>
                    </Card>
                </Col>
            </Row>
        </div>
    );
}
