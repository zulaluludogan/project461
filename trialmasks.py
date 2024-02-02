import cv2
import numpy as np
from cvzone.ColorModule import ColorFinder

# cap = cv2.VideoCapture('video5.mp4')
cap = cv2.VideoCapture(2)
# frameCounter = 0 

colorFinder = ColorFinder(False) # To Decide HSV values of objects "True"

## BOARD HSV ###
# hsvTargetVals = {'hmin': 124, 'smin': 45, 'vmin': 0, 'hmax': 23, 'smax': 255, 'vmax': 255}
hsvTargetVals1 = {'hmin': 123, 'smin': 47, 'vmin': 0, 'hmax': 179, 'smax': 255, 'vmax': 255}
hsvTargetVals2 = {'hmin': 0, 'smin': 47, 'vmin': 0, 'hmax': 18, 'smax': 255, 'vmax': 255}

hsvWhiteVals = {'hmin': 0, 'smin': 0, 'vmin': 226, 'hmax': 179, 'smax': 255, 'vmax': 255}# WHITE
hsvBlackVals =  {'hmin': 0, 'smin': 65, 'vmin': 0, 'hmax': 179, 'smax': 255, 'vmax': 96} # BLACK

hsvObstacleVals = {'hmin': 0, 'smin': 64, 'vmin': 0, 'hmax': 179, 'smax': 255, 'vmax': 91}
hsvPausePuck = {'hmin': 57, 'smin': 102, 'vmin': 135, 'hmax': 104, 'smax': 182, 'vmax': 237} # blue

hsvFullVals = {'hmin': 0, 'smin': 0, 'vmin': 0, 'hmax': 179, 'smax': 255, 'vmax': 255} # No contraint
# cornerPoints = [[58,129],[579,121],[62,448],[590,430]]  # board

hsvPuck1Vals = hsvWhiteVals   
hsvPuck2Vals = hsvBlackVals 

BoardSide = "left" # If it is "WALL", img should be rotated 180 degrees

def getBoard(img):
    global scale, START, cornerPoints, t, bh, bw
    scale = 1
    t = 10 
    bw, bh = 1110, 680 # board width, board height
    width, height = int(bw*scale),int(bh*scale)  #  the board size (height = 600 mm) width 1110mm

    if BoardSide == "WALL":
        img = cv2.rotate(img, cv2.ROTATE_180)

    maskObst = createHsvMask(img, hsvObstacleVals)
    contObstac =  detectContour(maskObst)
    obstacleEdgePoints = []

    if START < 5 :
        getPointArrays(contObstac,obstacleEdgePoints)
        obstacleEdgePoints = np.array(obstacleEdgePoints)

        left_upper = [np.min(obstacleEdgePoints[:, 0, 0]), np.min(obstacleEdgePoints[:, 0, 1])]
        left_lower = [np.min(obstacleEdgePoints[:, :, 0]), np.max(obstacleEdgePoints[:, :, 1])]
        right_upper = [np.max(obstacleEdgePoints[:, 1, 0]), np.min(obstacleEdgePoints[:, 1, 1])]
        right_lower = [np.max(obstacleEdgePoints[:, 2, 0]), np.max(obstacleEdgePoints[:, 2, 1])]
        cornerPoints = [[left_upper[0],left_upper[1]-t],[right_upper[0],right_upper[1]-t] ,[left_lower[0],left_lower[1]+t] ,[right_lower[0],right_lower[1]+t]]  

    pts1 =  np.float32(cornerPoints)
    pts2 =  np.float32([[0,0],[width,0],[0,height],[width,height]])
    matrix = cv2.getPerspectiveTransform(pts1,pts2)
    imgOutput = cv2.warpPerspective(img,matrix,(width, height))

    return imgOutput

# def getDistance(x1, y1, x2, y2):
#     global scale
#     distance = (((x1-x2)**2 + (y1-y2)**2)**0.5)/scale

#     return distance

def detectCircle(img, minRad,maxRad, minDista, hsvVals):
    global imgBoarder, maskTarget
    circleArray = []
    if hsvVals == hsvTargetVals1 :
        # maskCircle = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask1 = createHsvMask(img, hsvTargetVals1)
        mask2 = createHsvMask(img, hsvTargetVals2)
        maskCircle = mask1 + mask2
        maskTarget = maskCircle
    elif hsvVals == hsvBlackVals :
        maskCircle = createHsvMask(img, hsvVals)
        maskCircle [0:40][0:1110] = 0
        # cv2.imshow('maskCircle',maskCircle)
    else:
        maskCircle = createHsvMask(img, hsvVals)
    

    img_gray = cv2.medianBlur(maskCircle,5)
    circles = cv2.HoughCircles(img_gray,cv2.HOUGH_GRADIENT,1.5,minDist=minDista, param1=50,param2=23,minRadius = minRad,maxRadius = maxRad)
    try:
        circles = np.uint16(np.around(circles))
        for i in circles[0,:]:
            cv2.circle(imgBoarder,(i[0],i[1]),i[2],(0,255,0),2)  # draw the outer circle
            cv2.circle(imgBoarder,(i[0],i[1]),2,(0,255,0),3)     # draw the center of the circle
            circleArray.append([i[0],i[1],i[2]])
        # print("circle detected:",str(len(circles[0,:])))
        cv2.imshow('imgBoarder',imgBoarder)
    except:
        pass
    
    return circleArray

def createHsvMask(img,hsvVals):
    imgBlur = cv2.GaussianBlur(img, (5, 5), 2)
    imgColor, mask = colorFinder.update(imgBlur,hsvVals)
    kernel = np.ones((7,7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Difference btw dilation and erosion
    mask = cv2.medianBlur(mask, 5)
    # mask = cv2.dilate(mask, kernel, iterations=1)          # Increase white region
    # kernel = np.ones((11, 11), np.uint8)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) 
    # mask = cv2.erode(mask, kernel, iterations=1)
    # mask = cv2.medianBlur(mask, 5)
    return mask

def detectContour(mask):
    contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # cv2.CHAIN_APPROX_SIMPLE -> 4 points | cv2.CHAIN_APPROX_NONE -> all boundary points
    numberofObjects = len(contours)

    return contours

def findEdgePointsObst(cnt):
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
 
    # return [[int(box[0][0]),int(box[0][1])], [int(box[1][0]),int(box[1][1])],[int(box[2][0]),int(box[2][1])],[int(box[3][0]),int(box[3][1])]]
    return box 

def getPointArrays(contlist,pointlist):
    for cont in contlist:
        pts = findEdgePointsObst(cont)
        area = cv2.contourArea(pts)
        # print("area")
        # print(area)

        if area > 1700:   ### eliminate circles
            pointlist.append(pts)
    cv2.drawContours(imgBoarder, pointlist, -1, (0, 0, 255), 2)

START = 0

while True:
    success, img = cap.read()
    imgBoarder = img.copy()
    imgBoard = getBoard(img)
    if START < 5: 
        START += 1 
        maskFirstFrame = createHsvMask(imgBoard, hsvPuck2Vals)
    else: 
        pass
    
    imgBoarder = imgBoard.copy()
    
    maskTarget1 = createHsvMask(imgBoard, hsvTargetVals1)
    maskTarget2 = createHsvMask(imgBoard, hsvTargetVals2)
    maskObst = createHsvMask(imgBoard, hsvObstacleVals)
    maskPuck1 = createHsvMask(imgBoard, hsvPuck1Vals)
    maskPuck2 = createHsvMask(imgBoard, hsvPuck2Vals)
    
    # contPuck1 =  detectContour(maskPuck1)
    # contPuck2 =  detectContour(maskPuck2)
    
    obstacleEdgePoints = []
    maskObst[0:60][0:bw] = 0
    maskObst[bh-60:bh][0:bw] = 0
    contObstac =  detectContour(maskObst)
    getPointArrays(contObstac,obstacleEdgePoints)
    
    PuckBCenterRadius = detectCircle(imgBoard, 1, 70, 20, hsvPausePuck)
    targetCenterRadius = detectCircle(imgBoard, 50, 70, 40, hsvTargetVals1)
    Puck2CenterRadius = detectCircle(imgBoard, 5, 50, 10, hsvPuck2Vals)
    Puck1CenterRadius = detectCircle(imgBoard, 8, 50, 10, hsvPuck1Vals)

    diff = cv2.absdiff(maskPuck2, maskFirstFrame)
    threshold = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)[1]
    maskFirstFrame = createHsvMask(imgBoard, hsvPuck2Vals) 

    # maskFirstFrame =  createHsvMask(imgBoard, hsvPuck1Vals)+ createHsvMask(imgBoard, hsvPuck2Vals)
    print(threshold.sum())
    if threshold.sum() > 537580 :
        print("---motion is detected")
    cv2.imshow("threshold",threshold)

    # print("obstac", str(obstacleEdgePoints))
    # cv2.imshow("imgBoarder", imgBoarder)
    
    # cv2.imshow("maskPuck1",maskPuck1)
    # cv2.imshow("maskPuck2",maskPuck2)
    # cv2.imshow("maskTarget",maskTarget)
    # cv2.imshow("maskTarget",maskTarget)
    # cv2.imshow("maskObst", maskObst)

    # print("Number of  Puck1 = " + str(len(Puck1CenterRadius)))
    # print("Number of  Puck2 = " + str(len(Puck2CenterRadius)))
    # print("Number of  BLUE PUCK= " + str(len(PuckBCenterRadius)))
    # print("Number of  Target = " + str(len(targetCenterRadius))) 
    # print("Number of  Obstacles = " + str(len(obstacleEdgePoints)))

    
    # cv2.imshow("Image",img)
    # cv2.imshow("imgBoard",imgBoard)
    # cv2.imwrite("img.png",imgColor)
    # mm=cv2.imread('img.png')
    # cv2.imshow("hee",mm)
    
    cv2.waitKey(1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

