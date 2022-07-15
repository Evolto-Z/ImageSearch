import cv2 as cv
import os
from misc import adaptSizeToLimitedSize, alphaBlendAntiBG
import numpy as np

sift = cv.SIFT_create()
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
# search_params = dict(checks=50)
search_params = dict()
flann = cv.FlannBasedMatcher(index_params, search_params)

MINIMUM_SIZE = 64


class CorpusItem:
    nextUid = 0

    def __init__(self, path):
        self.path = ''
        self.kp = ()
        self.des = None
        self.uid = -1

        img = cv.imread(path, -1)
        if img is not None:
            self.path = path
            if img.ndim == 3 and img.shape[2] == 4:
                img = alphaBlendAntiBG(img)
            w, h = adaptSizeToLimitedSize(img.shape[1], img.shape[0], MINIMUM_SIZE, MINIMUM_SIZE, False)
            img = cv.resize(img, (w, h), interpolation=cv.INTER_LINEAR)
            try:
                self.kp, self.des = sift.detectAndCompute(img, None)
            except:
                img = cv.normalize(img, None, 0, 255, cv.NORM_MINMAX).astype('uint8')
                self.kp, self.des = sift.detectAndCompute(img, None)

            if self.isValid():
                self.uid = CorpusItem.nextUid
                CorpusItem.nextUid += 1

    def isValid(self):
        return len(self.kp) >= 2


class Corpus:
    def __init__(self, rootDir=''):
        self.rootDir = rootDir
        self.corpus = {}
        self.refresh()
        
    def refresh(self):
        if not self.rootDir:
            return

        for root, dirs, files in os.walk(self.rootDir):
            for file in files:
                if (file.endswith(('.jpg', '.png'))):
                    path = os.path.join(root, file)
                    item = CorpusItem(path)
                    if item.isValid():
                        self.corpus[item.uid] = item

    def search(self, kp, des):
        best = None
        bestMatches = []

        for item in self.corpus.values():
            query = (kp, des)
            train = (item.kp, item.des)
            if (len(query[0]) > len(train[0])):
                query, train = train, query

            matches = flann.knnMatch(query[1], train[1], k=2)

            tempGoodMatches = []
            for i in range(len(matches)):
                match = matches[i]
                if len(match) > 1:
                    m, n = match
                    if m.distance < 0.4 * n.distance:
                        tempGoodMatches.append(m)
                elif len(match) == 1:
                    tempGoodMatches.append(match[0])
            
            points1 = []
            points2 = []
            for match in tempGoodMatches:
                points1.append(query[0][match.queryIdx].pt)
                points2.append(train[0][match.trainIdx].pt)
            if len(points1) < 4 or len(points2) < 4:
                continue
            points1 = np.float32(points1)
            points2 = np.float32(points2)
            H, mask = cv.findHomography(points1, points2, cv.RANSAC)
            matchesMask = mask.ravel().tolist()

            goodMatches = []
            for i in range(len(matchesMask)):
                if matchesMask[i] == 1:
                    goodMatches.append(tempGoodMatches[i])

            if len(goodMatches) > len(bestMatches):
                best = item
                bestMatches = goodMatches
        
        return best, bestMatches


class CorpusCollection:
    def __init__(self):
        self.corpuses = {}

    def add(self, rootDir):
        if rootDir not in self.corpuses:
            self.corpuses[rootDir] = Corpus(rootDir)

    def remove(self, rootDir):
        if rootDir in self.corpuses:
            self.corpuses.pop(rootDir)

    def search(self, img):
        w, h = adaptSizeToLimitedSize(img.shape[1], img.shape[0], MINIMUM_SIZE, MINIMUM_SIZE, False)
        img = cv.resize(img, (w, h), interpolation=cv.INTER_LINEAR)
        kp = ()
        des = None
        try:
            kp, des = sift.detectAndCompute(img, None)
        except:
            img = cv.normalize(img, None, 0, 255, cv.NORM_MINMAX).astype('uint8')
            kp, des = sift.detectAndCompute(img, None)
        

        if len(kp) < 2:
            return None, []

        best = None
        bestMatches = []
        for corpus in self.corpuses.values():
            good, goodMatches = corpus.search(kp, des)
            if len(goodMatches) > len(bestMatches):
                best = good
                bestMatches = goodMatches
        
        return best, bestMatches

    def refresh(self, rootDir):
        if rootDir in self.corpuses:
            self.corpuses[rootDir].refresh()
        else:
            self.corpuses[rootDir] = Corpus(rootDir)
    
    def refreshAll(self):
        for corpus in self.corpuses.values():
            corpus.refresh()