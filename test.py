from zheye.zheye import zheye
z = zheye()
positions = z.Recognize('zhihu_captcha.png')
print(positions)