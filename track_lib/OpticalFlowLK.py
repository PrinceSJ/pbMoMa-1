import numpy as np
import cv2

cap = cv2.VideoCapture("mag_Videos/btfy/1.mp4")
imgPath = "mag_Videos/btfy/OFbtfy.jpg"

# ShiTomasi corner detection的参数
feature_params = dict(maxCorners=40,
                      qualityLevel=0.2,
                      minDistance=40,
                      blockSize=30)
# 光流法参数
# maxLevel 未使用的图像金字塔层数
lk_params = dict(winSize=(10,10),
                 maxLevel=1,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5, 0.01))

# 创建随机生成的颜色
color = np.random.randint(0, 255, (100, 3))


ret, old_frame = cap.read()                             # 取出视频的第一帧
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)  # 灰度化
p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
mask = np.zeros_like(old_frame)                         # 为绘制创建掩码图片

while True:
    ok, frame = cap.read()
    if not ok:
        print("Video over.")
        cv2.imwrite(imgPath,img)
        break
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 计算光流以获取点的新位置
    p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
    # 选择good points
    good_new = p1[st == 1]
    good_old = p0[st == 1]
    # 绘制跟踪框
    for i, (new, old) in enumerate(zip(good_new, good_old)):
        a, b = new.ravel()
        c, d = old.ravel()
        mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
        frame = cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
    img = cv2.add(frame, mask)
    cv2.imshow('frame', img)
    k = cv2.waitKey(30)  # & 0xff
    if k == 27:
        break
    old_gray = frame_gray.copy()
    p0 = good_new.reshape(-1, 1, 2)

cv2.destroyAllWindows()
cap.release()