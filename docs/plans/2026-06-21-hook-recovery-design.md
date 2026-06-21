# WeRead Hook 自动恢复设计

## 目标

解决连续导出过程中页面 Hook 偶发未注入，导致 `canvasContextHandler` 不存在、章节抓取中断的问题，同时保留现有章节缓存与断点续传行为。

## 设计

1. 在浏览器创建页面时，通过 `evaluateOnNewDocument` 注册 `hook.js`，确保每个新文档都在站点脚本运行前安装 Canvas Hook；移除旧的响应 HTML 改写路径，避免 Hook 被双重安装。
2. `goto_chapter` 在页面加载后检查 Hook 是否存在；缺失时重新注册并刷新当前章节，限定重试次数，避免无限循环。
3. `get_markdown` 不再直接让 JavaScript `ReferenceError` 泄漏，而是把 Hook 缺失或 Markdown 生成超时转换为 `LoadChapterFailedError`，交由现有的关闭浏览器、重新启动和断点续传流程恢复。
4. 章节 Markdown 仍然只在成功生成后落盘，已有文件继续跳过，不改变 EPUB 合成逻辑。

## 测试

- 单元测试验证 Hook 源码会被注册为新文档脚本。
- 单元测试模拟首次页面加载缺少 Hook，验证会刷新并在第二次检查成功。
- 单元测试验证 Hook 持续缺失及 Markdown 生成失败会转为 `LoadChapterFailedError`。
- 运行现有测试集，并使用已缓存书籍执行一次无缺章的 EPUB 合成验证。
