## Manifest V3 compatibility build / Manifest V3 兼容构建

For current Chromium versions, see the [reproducible MV3 build](mv3/README.md)
([中文](mv3/README.zh-CN.md)), with a packaged Vimium C bridge, installation steps,
checks and known limitations. This is an unofficial local build path; it does not
mean the original store listing has been updated.

### Legacy build / 旧版构建

PDF Viewer for Vimium C is a PDF Viewer supporting Vimium C shortcuts, and published on Chrome Web Store.

This folder stores parts of those diff files between the building files of standard PDF.js and PDF Viewer for Vimium C.

### Code difference

The code used to build is published on https://github.com/gdh1995/pdf.js/tree/master .

### Build steps

``` bash
# cd pdf.js
npm ci
gulp chromium
cd build-my
rm -rf chromium && cp -a ../build/chromium chromium
# copy these modified icon files to the "chromium/"
rm -rf dist && cp -a chromium dist
./minify.js
```
