"use client";

import Link from "next/link";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

export default function GuideVolcenginePage() {
    return (
        <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-slate-900">如何获取火山引擎 API Key？</h1>
                    <p className="mt-2 text-lg text-slate-600">
                        NanoBee PPT 使用火山引擎（Volcengine）提供的强大模型服务。
                    </p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>步骤 1：注册并登录火山引擎</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-slate-600">
                            访问火山引擎官网，点击右上角"登录/注册"。支持手机号快捷登录。
                        </p>
                        <div className="bg-slate-100 p-4 rounded-lg text-sm text-slate-500">
                            💡 新用户通常有免费额度，足够生成数百份 PPT。
                        </div>
                        <a
                            href="https://www.volcengine.com/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <Button variant="outline" className="w-full sm:w-auto">
                                🔗 前往火山引擎官网
                            </Button>
                        </a>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>步骤 2：开通模型推理服务 (Ark)</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-slate-600">
                            在控制台搜索 "火山方舟" (Ark)，或直接访问方舟控制台。
                        </p>
                        <ul className="list-disc pl-5 space-y-2 text-slate-600">
                            <li>点击左侧菜单的 <strong>开通管理</strong></li>
                            <li>开通 <strong>Doubao-pro-32k</strong> (用于生成文本)</li>
                            <li>注意：目前 SeaDream 图像生成通常包含在方舟服务中，或需单独申请内测。</li>
                        </ul>
                        <a
                            href="https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            <Button variant="outline" className="w-full sm:w-auto">
                                🔗 前往方舟控制台
                            </Button>
                        </a>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>步骤 3：创建 API Key</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-slate-600">
                            在方舟控制台左侧菜单找到 <strong>API Key 管理</strong>。
                        </p>
                        <ol className="list-decimal pl-5 space-y-2 text-slate-600">
                            <li>点击 <strong>创建 API Key</strong></li>
                            <li>复制生成的以 <code>sk-</code> 开头的密钥串</li>
                            <li>回到 NanoBee，将密钥粘贴在左下角的输入框中</li>
                        </ol>
                        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg text-sm text-yellow-800">
                            🔒 您的 API Key 仅保存在本地浏览器中，不会被上传到 NanoBee 服务器用于其他用途。
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-center pt-8">
                    <Link href="/">
                        <Button size="lg" className="px-8 shadow-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white border-0">
                            ← 返回 NanoBee 开始创作
                        </Button>
                    </Link>
                </div>
            </div>
        </div>
    );
}
