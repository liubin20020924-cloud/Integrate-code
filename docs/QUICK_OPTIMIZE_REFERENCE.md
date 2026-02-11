# 图片优化快速参考

## 立即执行（Windows）

```batch
# 双击运行或在命令行执行
optimize_all.bat
```

## 立即执行（Linux/Mac）

```bash
chmod +x optimize_all.sh
./optimize_all.sh
```

---

## 手动执行单个目录

### 优化首页图片
```bash
python scripts/optimize_images.py static/home/images -o static/home/images/optimized -q 80 -w 1400
```

### 优化工单系统图片
```bash
python scripts/optimize_images.py static/case/images -o static/case/images/optimized -q 80 -w 800
```

### 优化知识库图片
```bash
python scripts/optimize_images.py static/kb/images -o static/kb/images/optimized -q 80 -w 800
```

---

## 参数说明

- `-q 80`：质量（1-100），推荐 75-85
- `-w 1400`：最大宽度（首页推荐 1400，内部页面 800）
- `-r`：创建响应式图片（可选）

---

## 恢复原图

```bash
# Windows
copy static\home\images\backup\*.jpg static\home\images\

# Linux/Mac
cp static/home/images/backup/*.jpg static/home/images/
```

---

## 部署到服务器

```bash
# 上传优化后的图片
scp static/home/images/*.jpg user@server:/path/to/static/home/images/

# 或使用 rsync
rsync -avz static/home/images/ user@server:/path/to/static/home/images/
```

---

## Nginx 配置优化

将 `docs/nginx_image_optimization.conf` 的配置添加到 Nginx 配置文件。

```bash
# 编辑配置
sudo vi /etc/nginx/sites-available/your-site

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 在线工具

- TinyPNG：https://tinypng.com/（每月 20 张）
- Squoosh：https://squoosh.app/（免费，无限制）
- iLoveIMG：https://www.iloveimg.com/（免费）

---

## 查看优化效果

1. 打开 Chrome 浏览器
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 勾选 "Disable cache"
5. 刷新页面
6. 查看 Size 列和 Time 列

---

## 预期效果

| 图片 | 原始 | 优化后 | 节省 |
|------|------|--------|------|
| BJ2.jpg | 21.7 MB | ~3.5 MB | 84% |
| BJ5.jpg | 8.3 MB | ~1.8 MB | 78% |
| BJ1.jpg | 6.1 MB | ~1.2 MB | 80% |
| **总计** | **46.4 MB** | **~9.3 MB** | **80%** |

---

## 常见问题

**Q: 优化后质量变差？**
```bash
# 提高质量参数
python scripts/optimize_images.py static/home/images -q 85 -w 1400
```

**Q: BJ2.jpg 太大无法优化？**
```bash
# 降低质量和尺寸
python scripts/optimize_images.py static/home/images/BJ -q 60 -w 800
```

**Q: 想要更小的文件？**
```bash
# 降低质量到 70
python scripts/optimize_images.py static/home/images -q 70 -w 1000
```

---

## 完整文档

详细文档请查看：`docs/IMAGE_OPTIMIZATION_GUIDE.md`
