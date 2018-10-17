from numpy import *
import itertools
import csv 

support_dic = {}
 
 #生成原始数据，用于测试
def loadDataSet():
     with open(r'D:\datamining\Data mining HW1\Small_Data1.csv') as csvfile:

    # 讀取CSV檔案內容
      rows = csv.reader(csvfile)	
      data_set = []
    # 以迴圈輸出每一列
      for row in rows:
          data_set.append (row)
     return data_set
 
 #獲取整個數據庫中的一階元素
def createC1(dataSet):
     C1 = set([])
     for item in dataSet:
         C1 = C1.union(set(item))
     return [frozenset([i]) for i in C1]
 
 #輸入數據庫（dataset） 和 由第K-1層數據融合後得到的第K層數據集（Ck），
 #用最小支持度（minSupport)對 Ck 過濾，得到第k層剩下的數據集合（Lk）
def getLk(dataset, Ck, minSupport):
     global support_dic
     Lk = {}
     #計算Ck中每個元素在數據庫中出現次數
     for item in dataset:
         for Ci in Ck:
             if Ci.issubset(item):
                 if not Ci in Lk:
                     Lk[Ci] = 1
                 else:
                     Lk[Ci] += 1
     #用最小支持度過濾
     Lk_return = []
     for Li in Lk:
         support_Li = Lk[Li] / float(len(dataSet))
         if support_Li >= minSupport:
             Lk_return.append(Li)
             support_dic[Li] = support_Li
     return Lk_return
 
 #將經過支持度過濾後的第K層數據集合（Lk）融合
 #得到第k+1層原始數據Ck1
def genLk1(Lk):
     Ck1 = []
     for i in range(len(Lk) - 1):
         for j in range(i + 1, len(Lk)):
             if sorted(list(Lk[i]))[0:-1] == sorted(list(Lk[j]))[0:-1]:
                 Ck1.append(Lk[i] | Lk[j])
     return Ck1
 
 #遍歷所有二階及以上的頻繁項集合
def genItem(freqSet, support_dic):
     for i in range(1, len(freqSet)):
         for freItem in freqSet[i]:
             genRule(freItem)
 
 #輸入一個頻繁項，根據“信心值”生成規則
 #採用了遞歸，對規則樹進行剪枝
def genRule(Item, minConf=0.7):
     if len(Item) >= 2:
         for element in itertools.combinations(list(Item), 1):
             if support_dic[Item] / float(support_dic[Item - frozenset(element)]) >= minConf:
                 print (str([Item - frozenset(element)]) + "=>" + str(element))
                 print (support_dic[Item] / float(support_dic[Item - frozenset(element)])) 
                 genRule(Item - frozenset(element))
 
 #輸出結果
if __name__ == '__main__':
     dataSet = loadDataSet()
     result_list = []
     Ck = createC1(dataSet)
     #循環生成頻繁項集合，直至產生空集合
     while True:
         Lk = getLk(dataSet, Ck, 0.5)
         if not Lk:
             break
         result_list.append(Lk)
         Ck = genLk1(Lk)
         if not Ck:
             break
     #輸出頻繁項及其“支持度”
     print (support_dic)
     #輸出規則
     genItem(result_list, support_dic)