# Bilibili BV Video Downloader

[简体中文](README.md) | **English**

A Python command-line tool that accepts a BV ID, retrieves the corresponding Bilibili video, downloads its media streams, and uses FFmpeg to merge them into MP4 when needed.
It uses yt-dlp's Bilibili extractor to handle API signatures and media URLs. By default, it downloads the first part at the highest quality available to your current session and saves it to `downloads/<BV-ID>/` under the current working directory.

## 1. Create the Conda environment

Run the following commands from the project directory in Windows PowerShell. The initial installation requires an internet connection to download dependencies:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
conda activate .\.conda
```

`setup.ps1` sets a project-specific channel configuration and package cache for this installation to accommodate custom channel mappings on this machine. It does not modify the global Conda configuration. On a machine with a working channel configuration, you can also run `conda env create --prefix .\.conda --file environment.yml` directly.

The environment includes Python 3.11, FFmpeg, and the project dependencies. If Conda has not been initialized in your terminal, use the `conda run` command below without activating the environment.

## 2. Download a video by BV ID

```powershell
python download.py
```

Paste a BV ID at the prompt and press Enter. You can also pass it as an argument:

```powershell
python download.py BV1xx411c7mD
python download.py BV1xx411c7mD -o "D:\Videos\bilibili"
python download.py "https://www.bilibili.com/video/BV1xx411c7mD/?p=2"
```

To run without activating the environment:

```powershell
conda run --no-capture-output --prefix .\.conda python download.py BV1xx411c7mD
```

After installation, you can also use `bili-download BV1xx411c7mD` or `python -m bilibili_downloader BV1xx411c7mD`.
The BV ID above is an example; replace it with the ID of the video you want to download.

## Common options

```powershell
# Show the title, uploader, duration, and available resolutions without downloading
python download.py BV1xx411c7mD --info

# Download part 2; --page takes precedence over the URL's p parameter
python download.py BV1xx411c7mD --page 2

# Download all parts of this BV ID, without downloading the uploader's other videos
python download.py BV1xx411c7mD --all-parts

# Limit the resolution to 720p
python download.py BV1xx411c7mD --max-height 720

# Use a Netscape-format cookie file from your own signed-in account
python download.py BV1xx411c7mD --cookies cookies.txt

python download.py --help
```

Downloads display progress and automatically retry on network errors. Running the same command again resumes `.part` files or skips existing target files. Different quality levels use the same filenames by default; to download another quality level, specify a different output directory with `-o`.

## Troubleshooting

- **Lower quality than in the browser:** Available resolutions may be limited when you are not signed in. Use `--cookies` to supply your own login session. Download availability still depends on your account's access permissions.
- **403 / 412 / access checks or login prompts:** Confirm that you can watch the video in your browser, then try again later or supply a cookie file. The tool does not automatically read browser login information. Cookies are login credentials; do not share them or commit them to Git. Files matching `cookies*.txt` are ignored by default.
- **Unable to retrieve video information:** Check the BV ID, network connection, and whether the video has been deleted or made private. If the site's API changes, run `python -m pip install -U yt-dlp` inside the project environment.
- **FFmpeg not found:** Make sure the project environment is activated, or run `conda install -c conda-forge ffmpeg` inside it.
- **Supported input:** Full BV IDs and `bilibili.com/video/BV...` links are supported. `b23.tv` short links, bangumi links, and AV IDs are not supported.

## Development and checks

```powershell
python -m unittest discover -s tests -v
```

`src/bilibili_downloader/cli.py` contains input validation, download options, and the command-line logic. `download.py` is the convenience entry point, and `environment.yml` defines the Conda environment. Tests use a mock downloader and do not require network access.

Technical references: [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp) and [Bilibili extractor](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/bilibili.py).
