# Bilibili BV 视频下载器

**简体中文** | [English](README.en.md)

Python 命令行项目：输入 BV 号，自动解析视频、下载音视频并通过 FFmpeg 合并为 MP4。
使用 yt-dlp 的 Bilibili 提取器处理接口签名和媒体地址。默认下载第 1 P、当前访问权限下的最高可用清晰度，保存至当前工作目录的 `downloads/<BV号>/`。

## 1. 创建 Conda 环境

在项目目录运行（首次需要联网下载依赖）：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
conda activate .\.conda
```

`setup.ps1` 仅为本次安装设置项目级频道配置和包缓存，兼容本机自定义频道映射，不修改全局 Conda 配置。其他配置正常的电脑也可直接运行 `conda env create --prefix .\.conda --file environment.yml`。

环境包含 Python 3.11、FFmpeg 和项目依赖。如果终端尚未初始化 Conda，可直接使用下面的 `conda run`，无需激活。

## 2. 输入 BV 号下载

```powershell
python download.py
```

根据提示粘贴 BV 号并回车。也可以直接传入参数：

```powershell
python download.py BV1xx411c7mD
python download.py BV1xx411c7mD -o "D:\Videos\bilibili"
python download.py "https://www.bilibili.com/video/BV1xx411c7mD/?p=2"
```

不激活环境时：

```powershell
conda run --no-capture-output --prefix .\.conda python download.py BV1xx411c7mD
```

安装后还可以使用 `bili-download BV1xx411c7mD` 或 `python -m bilibili_downloader BV1xx411c7mD`。
上面的 BV 号仅是用法示例，请换成目标视频的真实 BV 号。

## 常用选项

```powershell
# 查询标题、UP 主、时长和可用分辨率，不下载
python download.py BV1xx411c7mD --info

# 下载第 2 P；--page 优先于链接中的 p 参数
python download.py BV1xx411c7mD --page 2

# 下载这个 BV 的所有分 P，不下载 UP 主的其他视频
python download.py BV1xx411c7mD --all-parts

# 最高 720p
python download.py BV1xx411c7mD --max-height 720

# 使用自己登录账号的 Netscape 格式 Cookie 文件
python download.py BV1xx411c7mD --cookies cookies.txt

python download.py --help
```

下载显示进度，网络异常自动重试，重复执行相同命令会续传 `.part` 文件或跳过已存在的目标文件。不同清晰度默认共用文件名；要重新下载另一清晰度，请指定不同的 `-o` 目录。

## 常见问题

- **下载清晰度比网页低**：未登录账号可获取的清晰度可能受限，可以通过 `--cookies` 提供自己的登录状态；可下载的内容仍由账号权限决定。
- **403 / 412 / 风控或登录提示**：先确认浏览器可以观看，稍后重试或提供 Cookie。程序不会自动读取浏览器登录信息。Cookie 是登录凭证，请勿分享或提交到 Git；默认 `cookies*.txt` 已被忽略。
- **无法获取视频信息**：检查 BV 号、网络及视频是否已删除/设为私密；接口变化时，在项目环境中执行 `python -m pip install -U yt-dlp`。
- **找不到 FFmpeg**：确认已激活项目环境，或在环境中运行 `conda install -c conda-forge ffmpeg`。
- **输入格式**：支持完整 BV 号及 `bilibili.com/video/BV...` 链接，不支持 `b23.tv` 短链接、番剧链接或 AV 号。

## 开发与检查

```powershell
python -m unittest discover -s tests -v
```

`src/bilibili_downloader/cli.py` 包含输入校验、下载参数和命令行逻辑；`download.py` 是便捷入口；`environment.yml` 定义 Conda 环境。测试使用模拟下载器，不依赖网络。

技术参考：[yt-dlp 官方文档](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp)、[Bilibili 提取器](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/bilibili.py)。
