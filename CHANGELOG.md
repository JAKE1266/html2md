# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.1] - 2026-11-27

### 修复
- 标题中的粗体、斜体、代码、删除线、链接与图片保留在同一标题行
- 未闭合标题在下一个块级元素开始时正确收尾
- Windows 默认编码下 CLI 的 UTF-8 标准输入、输出与错误流

### 变更
- PyPI 发行名改为 `html2md-kit`，Python 模块名与 `html2md` 命令保持不变
- CI 增加 wheel/sdist 构建、元数据检查与真实安装冒烟，覆盖三系统 × 四个 Python 版本
- Ubuntu 固定为 22.04，macOS 使用 Intel runner，兼容 Python 3.8/3.9

### 新增
- 6 个标题回归用例与 2 个 CLI 编码/版本用例，共 46 个单元测试
- sdist 清单与已安装发行包冒烟脚本

## [0.1.0] - 2026-11-21

### 新增
- 核心功能实现(纯标准库,零第三方依赖)
- CLI 命令行入口
- 38 个单元测试
- GitHub Actions 三系统 × 多版本 CI
- 中文 README 与 MIT 许可证

### 变更
- 补齐徽章、项目结构与本日志,与其他仓库文档标准统一
