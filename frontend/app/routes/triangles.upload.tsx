import React, { useState } from "react";
import type { ActionFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useActionData, useNavigation, useSubmit } from "@remix-run/react";
import {
    Form,
    Upload,
    Button,
    Input,
    Switch,
    Card,
    Alert,
    Table,
    Typography,
    Space,
    message,
    Spin
} from "antd";
import { UploadOutlined, SendOutlined } from "@ant-design/icons";
import { apiClient, type TriangleAnalysisResponse } from "~/utils/api.server";

const { Title, Text } = Typography;

interface ActionData {
    success?: boolean;
    error?: string;
    result?: TriangleAnalysisResponse;
}

export async function action({ request }: ActionFunctionArgs) {
    try {
        const formData = await request.formData();
        const csv = formData.get("csv") as File;
        const origin_col = formData.get("origin_col") as string || "origin";
        const dev_col = formData.get("dev_col") as string || "dev";
        const value_col = formData.get("value_col") as string || "value";
        const cumulative = formData.get("cumulative") === "true";

        if (!csv) {
            return json<ActionData>({
                success: false,
                error: "Please select a CSV file"
            });
        }

        // Call the API
        const result = await apiClient.analyzeTriangle({
            csv,
            origin_col,
            dev_col,
            value_col,
            cumulative
        });

        return json<ActionData>({
            success: true,
            result
        });

    } catch (error) {
        return json<ActionData>({
            success: false,
            error: error instanceof Error ? error.message : "An error occurred"
        });
    }
}

export default function UploadTriangle() {
    const actionData = useActionData<ActionData>();
    const navigation = useNavigation();
    const submit = useSubmit();
    const [fileList, setFileList] = useState<any[]>([]);
    const [form] = Form.useForm();

    const isSubmitting = navigation.state === "submitting";

    const handleSubmit = async (values: any) => {
        if (fileList.length === 0) {
            message.error("Please select a CSV file");
            return;
        }

        const formData = new FormData();
        formData.append("csv", fileList[0].originFileObj);
        formData.append("origin_col", values.origin_col || "origin");
        formData.append("dev_col", values.dev_col || "dev");
        formData.append("value_col", values.value_col || "value");
        formData.append("cumulative", values.cumulative !== false ? "true" : "false");

        submit(formData, { method: "post", encType: "multipart/form-data" });
    };

    const uploadProps = {
        beforeUpload: () => false, // Prevent auto upload
        fileList,
        onChange: ({ fileList }: any) => setFileList(fileList),
        accept: ".csv",
    };

    const ldfColumns = [
        {
            title: "Origin Period",
            dataIndex: "origin",
            key: "origin",
        },
        {
            title: "Development Period",
            dataIndex: "development",
            key: "development",
        },
        {
            title: "LDF",
            dataIndex: "ldf",
            key: "ldf",
            render: (value: number | null) => value?.toFixed(4) || "N/A",
        },
    ];

    return (
        <div>
            <Title level={2}>Upload Triangle</Title>

            <Card title="Triangle Data Upload" style={{ marginBottom: 24 }}>
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{
                        origin_col: "origin",
                        dev_col: "dev",
                        value_col: "value",
                        cumulative: true,
                    }}
                >
                    <Form.Item
                        label="CSV File"
                        required
                        help="Upload a CSV file with columns for origin period, development period, and values"
                    >
                        <Upload {...uploadProps}>
                            <Button icon={<UploadOutlined />}>Select CSV File</Button>
                        </Upload>
                    </Form.Item>

                    <Form.Item label="Origin Column Name" name="origin_col">
                        <Input placeholder="origin" />
                    </Form.Item>

                    <Form.Item label="Development Column Name" name="dev_col">
                        <Input placeholder="dev" />
                    </Form.Item>

                    <Form.Item label="Value Column Name" name="value_col">
                        <Input placeholder="value" />
                    </Form.Item>

                    <Form.Item label="Cumulative Values" name="cumulative" valuePropName="checked">
                        <Switch />
                    </Form.Item>

                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            icon={<SendOutlined />}
                            loading={isSubmitting}
                            disabled={fileList.length === 0}
                        >
                            Analyze Triangle
                        </Button>
                    </Form.Item>
                </Form>
            </Card>

            {actionData?.error && (
                <Alert
                    message="Error"
                    description={actionData.error}
                    type="error"
                    showIcon
                    style={{ marginBottom: 24 }}
                />
            )}

            {actionData?.success && actionData.result && (
                <div>
                    <Title level={3}>Analysis Results</Title>

                    <Space direction="vertical" size="large" style={{ width: "100%" }}>
                        <Card title="Ultimate Estimates" size="small">
                            <Space size="large">
                                <div>
                                    <Text strong>Mack Ultimate:</Text>
                                    <br />
                                    <Text style={{ fontSize: "18px", color: "#1890ff" }}>
                                        {actionData.result.mack_ultimate?.toLocaleString() || "N/A"}
                                    </Text>
                                </div>
                                {actionData.result.mack_mse && (
                                    <div>
                                        <Text strong>Mack MSE:</Text>
                                        <br />
                                        <Text style={{ fontSize: "18px", color: "#722ed1" }}>
                                            {actionData.result.mack_mse.toLocaleString()}
                                        </Text>
                                    </div>
                                )}
                                {actionData.result.cape_cod_ultimate && (
                                    <div>
                                        <Text strong>Cape Cod Ultimate:</Text>
                                        <br />
                                        <Text style={{ fontSize: "18px", color: "#52c41a" }}>
                                            {actionData.result.cape_cod_ultimate.toLocaleString()}
                                        </Text>
                                    </div>
                                )}
                            </Space>
                        </Card>

                        {actionData.result.ldfs.length > 0 && (
                            <Card title="Age-to-Age LDFs" size="small">
                                <Table
                                    dataSource={actionData.result.ldfs}
                                    columns={ldfColumns}
                                    pagination={false}
                                    size="small"
                                    rowKey={(record) => `${record.origin}-${record.development}`}
                                />
                            </Card>
                        )}
                    </Space>
                </div>
            )}

            {isSubmitting && (
                <div style={{ textAlign: "center", padding: "40px" }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>
                        <Text>Analyzing triangle data...</Text>
                    </div>
                </div>
            )}
        </div>
    );
}
