# [Tool Kit] 维视相机的自动拍照
使用方法：
将 test.py 放入维视相机的 Sample Python SDK 中运行

## 注意事项
自动拍照的实现原理是模仿鼠标的点击
在保存图像前，有一个 for loop 监测返回信号，确保已经获取了最终图片
