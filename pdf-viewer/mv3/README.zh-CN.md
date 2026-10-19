# Vimium C PDF 阅读器：Manifest V3 兼容构建

[English](README.md) · [验收与限制](VALIDATION.md)

这是一套**非官方、可本地加载的兼容构建方案**：在新版 PDF.js Chromium 阅读器中接入已有 Vimium C，复用快捷键设置，支持远端与本地 PDF。
它不代表原 Chrome 应用商店扩展已更新，也不承诺本 PR 一定被合并或发布。

## 修复了什么

旧阅读器仍使用 Manifest V2、常驻后台页面与阻塞式 webRequest；直接修改 manifest_version 无法完成迁移。
这里使用 Mozilla 已实现的 Manifest V3 阅读器，只补接 Vimium C：

| 问题 | 处理 |
|---|---|
| 旧后台与 PDF 拦截 API 不兼容 | 使用 PDF.js 的原生 MV3 Chromium 构建 |
| MV3 不允许从另一个扩展执行脚本 | 将匹配的 Vimium 前端打包在阅读器内，连接原 Vimium C 后台 |
| 阅读器 CSP 阻止链接提示和搜索框样式 | 仅放行内联 CSS，保留本地脚本策略 |
| 前端快照与已更新后台可能不匹配 | 校验版本、构建标识与脚本来源；不匹配则停止注入并提示 |

固定来源：PDF.js **v6.4.299**（`d0991a0d53f3bb3a7307e3b83f279c1d117aafb3`），Chrome 商店版 Vimium C **2.12.2**（build `9e78033`）。
约 108 KB 的 Vimium 前端文件附原始哈希与完整许可证；不包含用户设置、历史记录或浏览器 profile。

## 构建与安装

需要 Python **3.12+**、Node.js **22**、npm；工作目录和输出目录都必须是尚不存在的新目录。

```sh
python3 pdf-viewer/mv3/build.py \
  --work-dir /绝对路径/新的临时构建目录 \
  --output /绝对路径/长期保留的阅读器目录
python3 -m unittest discover -s pdf-viewer/mv3/tests -v
```

脚本下载固定 PDF.js 源码、按 lockfile 安装依赖并编译，不读取本机浏览器资料。
临时构建目录可能占用数百 MB，构建完成后可删除；**安装目录需要长期保留**。
`BUILD_INFO.json` 记录源码版本和 commit，`SHA256SUMS.json` 记录产物哈希；不保证跨操作系统字节完全相同。
源码归档没有 Git 历史，PDF.js 内部引擎版本可能显示 `6.4.0`，真实来源以 BUILD_INFO 中固定 commit 为准。

1. 保留或安装官方 Vimium C **2.12.2**。
2. 在 `chrome://extensions` 开启开发者模式，选择“加载未打包的扩展程序”，加载输出目录。
3. 将新阅读器 ID 追加到 Vimium C 选项的“受信任的其它扩展”，保存，保留原列表。
4. 在阅读器详情页开启“允许访问文件网址”。
5. 如果其他 PDF 扩展抢先接管，停用冲突阅读器，再从原始 URL 打开文件。

未打包扩展的 ID 与安装路径有关，请使用自己实际显示的 ID；本方案不会冒用原商店扩展身份，也不会自动安装或修改权限。

## 使用与限制

- `j/k` 滚动，`20j` 等计数有效；`gg/G` 首尾跳转；`f` 显示链接和按钮提示。
- 原 Vimium 自定义映射继续生效；`d/u` 的具体动作取决于原设置，不修改默认映射。
- **`/` 只搜索当前已渲染文字，PDF 全文搜索请用 `⌘F`（macOS）或 `Ctrl+F`。** 实测同一文件 `/` 随渲染状态得到 11 或 32 处，而全文搜索为 42 处。
- 继承 PDF.js 所需的网站、请求和导航权限，范围较广；本地文件访问单独由浏览器开关控制。
- 保留脚本 CSP 的 `self` 与 PDF.js 所需 `wasm-unsafe-eval`，不加载远程可执行脚本；只为 Vimium 动态提示放行内联 CSS。
- 本构建不加载上游后台 telemetry 模块，不增加上传服务；远端文件仍向原服务器请求。
- Vimium C 升级后可能需要重新审查并更新前端快照；不匹配时 PDF 仍可阅读，但快捷键连接停止。
- 未承诺旧版全部功能一致；无痕、登录态/POST/嵌入式 PDF、扫描件 OCR 等边界见 [验收记录](VALIDATION.md)。

## 维护与许可证

刷新依赖时仅复制 `vendor/vimium-c/snapshot.json` 列出的四个官方代码文件，保留许可证，核对注入协议后更新版本、构建标识和哈希，并重新测试。
不要提交浏览器配置、Cookie、凭据、私有文件或整份 profile；生成的 PDF.js 安装包不进入 Git。

卸载时在 Chrome 删除本阅读器，并移除 Vimium C 中对应的信任 ID；原 Vimium C 和快捷键配置继续保留。
集成代码采用本仓库 MIT 许可证；PDF.js 采用 Apache-2.0；Vimium C 的 Apache-2.0／历史 MIT 声明保留在 [上游许可证](vendor/vimium-c/LICENSE.txt)。
