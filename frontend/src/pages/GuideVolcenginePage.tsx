import { Link } from "@tanstack/solid-router";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

export function GuideVolcenginePage() {
  return (
    <div class="space-y-6">
      <div class="text-center space-y-2">
        <h1 class="text-3xl font-bold text-slate-900">如何获取火山引擎 API Key？</h1>
        <p class="text-lg text-slate-600">NanoBee PPT 使用火山引擎（Volcengine）提供的模型服务。</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤 1：注册并登录火山引擎</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <p class="text-slate-600">访问火山引擎官网，点击右上角"登录/注册"。支持手机号快捷登录。</p>
          <div class="bg-slate-100 p-4 rounded-lg text-sm text-slate-500">💡 新用户通常有免费额度，足够生成数百份 PPT。</div>
          <a href="https://www.volcengine.com/" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" class="w-full sm:w-auto">🔗 前往火山引擎官网</Button>
          </a>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤 2：开通模型推理服务 (Ark)</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <p class="text-slate-600">在控制台搜索 "火山方舟" (Ark)，或直接访问方舟控制台。</p>
          <ul class="list-disc pl-5 space-y-2 text-slate-600">
            <li>点击左侧菜单的 <strong>模型推理 &gt; 在线推理 &gt; 创建推理接入点</strong></li>
            <li>文本模型：选择 <strong>doubao-seed-1.6</strong> 接入点</li>
            <li>图像模型：选择 <strong>doubao-seedream-4.5</strong></li>
            <li>
              <span class="font-semibold text-red-600">重要提示：</span> 默认公共接入点 ID：
              <ul class="list-disc pl-5 mt-1 text-sm font-mono text-slate-500">
                <li>文本: doubao-seed-1-6-251015</li>
                <li>图像: doubao-seedream-4-5-251128</li>
              </ul>
            </li>
          </ul>
          <a
            href="https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" class="w-full sm:w-auto">🔗 前往方舟控制台</Button>
          </a>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤 3：创建 API Key</CardTitle>
          <CardDescription>密钥仅保存在本地浏览器中，不会被上传。</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <ol class="list-decimal pl-5 space-y-2 text-slate-600">
            <li>在方舟控制台选择 <strong>API Key 管理</strong></li>
            <li>点击 <strong>创建 API Key</strong> 并复制以 <code>sk-</code> 开头的密钥</li>
            <li>回到 NanoBee，在调用后端接口前填入密钥</li>
          </ol>
          <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg text-sm text-yellow-800">
            🔒 建议将密钥保存到环境变量或本地配置文件，避免泄露。
          </div>
        </CardContent>
      </Card>

      <div class="flex justify-center pt-4">
        <Link to="/">
          <Button class="px-8">← 返回 NanoBee</Button>
        </Link>
      </div>
    </div>
  );
}
