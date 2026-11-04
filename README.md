[English](README_en.md) | [简体中文](README.md)

<div align="center">
  <img src="icons/icon.png" alt="icon" width="200"><br>
  <h1>ok-dna</h1>
  <p>一款基于图像识别的《二重螺旋》自动化工具，支持后台运行。</p>
  <p>基于 <a href="https://github.com/ok-oldking/ok-script">ok-script</a> 框架开发。</p>
  
  <p>
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="平台">
    <img src="https://img.shields.io/badge/python-3.12-skyblue" alt="Python版本">
    <a href="https://github.com/BnanZ0/ok-duet-night-abyss/releases"><img src="https://img.shields.io/github/downloads/BnanZ0/ok-duet-night-abyss/total" alt="总下载量"></a>
    <a href="https://github.com/BnanZ0/ok-duet-night-abyss/releases"><img src="https://img.shields.io/github/v/release/BnanZ0/ok-duet-night-abyss" alt="最新版本"></a>
    <a href="https://discord.gg/vVyCatEBgA"><img alt="Discord" src="https://img.shields.io/discord/296598043787132928?color=5865f2&label=%20Discord"></a>
  </p>
</div>

## ⚠️ 免责声明

本软件为开源、免费的外部工具，仅供学习和交流使用，旨在通过模拟操作简化《二重螺旋》的游戏玩法。

-   **工作原理**：程序仅通过识别现有用户界面与游戏进行交互，不修改任何游戏文件或代码。
-   **使用目的**：旨在为用户提供便利，无意破坏游戏平衡或提供任何不公平优势。
-   **法律责任**：使用本软件产生的所有问题及后果，均与本项目及开发者团队无关。开发者团队拥有对本项目的最终解释权。
-   **商业行为**：若您遇到商家使用本软件进行代练并收费，此行为可能涉及设备与时间成本，与本软件本身无关。

> **请注意：根据[《二重螺旋》公平游戏宣言](https://dna.yingxiong.com/#/news/list?id=14453&type=2523)：**
>
> > "严禁使用任何外挂、第三方工具以及其他破坏游戏公平性的行为。"
> > "一经核实，运营团队将根据情节严重程度和次数，采取扣除违规收益、冻结或永久封禁游戏账号等措施，以维护玩家的公平权益。"
>
> **您应充分了解并自愿承担使用本工具可能带来的所有风险。**

<details>
<summary><strong>Disclaimer in English</strong></summary>

This software is an open-source, free external tool intended for learning and exchange purposes only. It is designed to automate the gameplay of *Duet Night Abyss* by interacting with the game solely through the existing user interface and in compliance with relevant laws and regulations. The package is intended to provide a simplified way for users to interact with the game and is not meant to disrupt the game balance or provide any unfair advantage. This package does not modify any game files or game code in any way.

All issues and consequences arising from the use of this software are not related to this project or its development team. The development team reserves the final right of interpretation for this project. If you encounter vendors using this software for services and charging a fee, this may cover their costs for equipment and time; any resulting problems or consequences are not associated with this software.
</details>

## ✨ 主要功能

<img width="100%" alt="功能演示" src="https://github.com/user-attachments/assets/cb7f145b-b304-4a0e-891a-3b6d5acff65d" />

*   **副本自动挂机**
    *   支持全自动与半自动模式
    *   自动连战
    *   兼容外部移动逻辑 (Mod)
*   **自动钓鱼** (核心逻辑原作者: B站 @无敌大蜜瓜)
*   **快速移动**
    *   自动穿引共鸣
*   **自动花序弓蓄力**
*   **后台运行**
    *   支持 PC 版游戏在后台运行时进行自动化操作

## 🖥️ 运行环境与兼容性

*   **操作系统**：Windows
*   **游戏分辨率**：1600x900 或更高（推荐 16:9 宽高比）
*   **游戏语言**：简体中文 / English

## 🚀 安装指南

### 方式一：使用安装包 (推荐)

此方法适合绝大多数用户，简单快捷，并支持自动更新。

1.  前往 [**Releases**](https://github.com/BnanZ0/ok-duet-night-abyss/releases) 页面。
2.  下载最新的 `ok-dna-win32-China-setup.exe` 文件。
3.  双击运行安装程序，按提示完成安装即可。

### 方式二：从源码运行 (适合开发者)

此方法需要您具备 Python 环境，适合希望进行二次开发或调试的用户。

1.  **环境要求**：确保已安装 **Python 3.12** 或更高版本。
2.  **克隆仓库**：
    ```bash
    git clone https://github.com/BnanZ0/ok-duet-night-abyss.git
    cd ok-duet-night-abyss
    ```
3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt --upgrade
    ```
    *提示：每次更新代码后，建议重新运行此命令以确保依赖库为最新版本。*
4.  **运行程序**：
    ```bash
    # 运行正式版
    python main.py
    
    # 运行调试版 (会输出更详细的日志)
    python main_debug.py
    ```

## 📖 使用指南与 FAQ

为确保程序稳定运行，请在使用前仔细阅读以下配置要求和常见问题解答。

### 一、 使用前配置 (必读)

在启动自动化前，请务必检查并确认以下设置：

*   **图形设置**
    *   **显卡滤镜**：**关闭** 所有显卡滤行和锐化效果（如 NVIDIA Freestyle, AMD FidelityFX）。
    *   **游戏亮度**：使用游戏 **默认亮度**。
    *   **游戏UI缩放**：使用游戏 **默认缩放100%**。
*   **分辨率**
    *   推荐使用 **1600x900** 或以上的主流分辨率。
*   **按键设置**
    *   请务必使用游戏 **默认** 按键绑定。
*   **第三方软件**
    *   关闭任何在游戏画面上显示信息的悬浮窗，如 MSI Afterburner (小飞机) 的 **帧率显示**。
*   **窗口与系统状态**
    *   **鼠标干扰**：当游戏窗口处于 **前台** 时，请勿移动鼠标，否则会干扰程序的模拟点击。
    *   **窗口状态**：游戏窗口可以置于后台，但 **不可最小化**。
    *   **系统状态**：请勿让电脑 **熄屏** 或 **锁屏**，否则将导致程序中断。

### 二、 快速上手

1.  进入您想要自动化的关卡或场景。
2.  在程序界面上点击 **“开始”** 按钮即可。

### 三、 安装外部逻辑 (Mod)

您可以安装社区开发的外部逻辑模块来扩展程序功能。

1.  在程序主页，点击 **“安装目录”** 按钮打开程序文件夹。
2.  将下载的 Mod 文件放入 `mod` 文件夹内。
3.  重启程序即可加载。

### 四、 常见问题解答 (FAQ)

**Q1: 角色移动时经常撞墙，或者无法准确走到目标点？**

*   **原因**：游戏引擎的移动速度与帧率 (FPS) 强相关。
*   **解决方案**：
    1.  **调整游戏帧率**：在游戏设置中，依次尝试将帧率上限设为 **60 FPS** / **120 FPS** / **无限制**，找到表现最稳定的一档。
    2.  **调整按键时长**：在对应任务或 Mod 的设置中，微调 **按键时长** 参数。
    3.  **等待官方优化**：此问题可能需要等待游戏官方后续更新修复。

**Q2: 我安装的 Mod 没有生效，或者识别不正确？**

*   **原因**：Mod 内置的图像识别素材可能无法适配所有分辨率。
*   **解决方案**：
    1.  **切换分辨率**：尝试更换一个常见分辨率（如 1920x1080 或 1600x900）。
    2.  **手动更新素材**：如果您了解 Mod 制作，可以为您当前的分辨率重新录制识图所需的截图。

**Q3: 程序卡在结算或复位界面，不再继续执行？**

*   **原因**：很可能是无意的鼠标移动干扰了程序的图像识别。
*   **解决方案**：
    1.  在程序左下角点击 **“设置”**。
    2.  切换到 **“挂机设置”** 选项卡。
    3.  勾选并启用 **“防止鼠标干扰”** 功能。

### 五、 问题反馈

如果以上方法未能解决您的问题，欢迎通过 [**Issues**](https://github.com/BnanZ0/ok-duet-night-abyss/issues) 向我们反馈。为帮助我们快速定位问题，请在提交时提供以下信息：

*   **问题截图**：清晰展示异常界面或错误提示。
*   **日志文件**：附上程序目录下的 `.log` 日志文件。
*   **详细描述**：您进行了哪些操作？问题具体表现是什么？问题是稳定复现还是偶尔发生？

## 💬 社区与交流

*   **Discord**: [https://discord.gg/vVyCatEBgA](https://discord.gg/vVyCatEBgA)

## 🔗 使用[ok-script](https://github.com/ok-oldking/ok-script)开发的项目：

* 鸣潮 [https://github.com/ok-oldking/ok-wuthering-wave](https://github.com/ok-oldking/ok-wuthering-waves)
* 原神(停止维护,
  但是后台过剧情可用) [https://github.com/ok-oldking/ok-genshin-impact](https://github.com/ok-oldking/ok-genshin-impact)
* 少前2 [https://github.com/ok-oldking/ok-gf2](https://github.com/ok-oldking/ok-gf2)
* 星铁 [https://github.com/Shasnow/ok-starrailassistant](https://github.com/Shasnow/ok-starrailassistant)
* 星痕共鸣 [https://github.com/Sanheiii/ok-star-resonance](https://github.com/Sanheiii/ok-star-resonance)
* 二重螺旋 [https://github.com/BnanZ0/ok-duet-night-abyss](https://github.com/BnanZ0/ok-duet-night-abyss)
* 白荆回廊(停止更新) [https://github.com/ok-oldking/ok-baijing](https://github.com/ok-oldking/ok-baijing)
