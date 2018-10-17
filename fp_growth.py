# encoding: utf-8

# 從fp_growth算是導入find_frequent_itemsets
# find_frequent_itemsets（trans，min_support）

from collections import defaultdict, namedtuple
import csv

def find_frequent_itemsets(trans, min_support, include_support=False):    
    #1.Run出給定frequent itemsets
    #2.trans可以是任何可迭代的項目
    #3.min_support設定itemsets的最少值
    #4.include_support如果是true則會顯示support值,false則不會(最下方我設定true)
    
    # mapp出items的support值
    items = defaultdict(lambda: 0)

    # Load導入的trans然後計算support值
    # 有哪些items.
    for transaction in trans:
        for item in transaction:
            items[item] += 1

    # 刪掉小於min_support的items
    items = dict((item, support) for item, support in items.items()
        if support >= min_support)

    # 構建FP_tree
    # 在將任何trans添加到tree之前，先去除不頻繁的項目(小於min_support的itemsets)
    # 按照頻率的降序對剩下的項目進行排序
    def clean_transaction(transaction):
        transaction = filter(lambda v: v in items, transaction)
        transaction_list = list(transaction)   # 引入臨時變量transaction_list
        transaction_list.sort(key=lambda v: items[v], reverse=True)
        return transaction_list

    master = FPTree()
    for transaction in map(clean_transaction, trans):
        master.add(transaction)

    def find_with_suffix(tree, suffix):
        for item, nodes in tree.items():
            support = sum(n.count for n in nodes)
            if support >= min_support and item not in suffix:
                # New winner!
                found_set = [item] + suffix
                yield (found_set, support) if include_support else found_set

                # 構建tree的條件並遞歸搜索其中的frequent_itemsets。
                cond_tree = conditional_tree_from_paths(tree.prefix_paths(item))
                for s in find_with_suffix(cond_tree, found_set):
                    yield s # 回傳新的itemsets

    # 搜索frequent_itemsets，並回傳結果
    for itemset in find_with_suffix(master, []):
        yield itemset

class FPTree(object):
    
    Route = namedtuple('Route', 'head tail')

    def __init__(self):
        # tree的root node
        self._root = FPNode(self, None, None)

        # 將itemset mapping到paths的頭部和尾部，paths將包含該項目的每個節點。
        self._routes = {}

    @property
    def root(self):
        # tree的root node
        return self._root

    def add(self, transaction):
        # 加入transaction到tree
        point = self._root

        for item in transaction:
            next_point = point.search(item)
            if next_point:
                # 這個tree中已存在當前transaction item的node; 繼續用它。
                next_point.increment()
            else:
                # 創建一個新的點並將它加到我們當前正在查看的點的child。
                next_point = FPNode(self, item)
                point.add(next_point)

                # 更新包含此item的node的route然後添加新節點。
                self._update_route(next_point)

            point = next_point

    def _update_route(self, point):
        # 通過此item的所有node來增加給定node的route
        assert self is point.tree

        try:
            route = self._routes[point.item]
            route[1].neighbor = point # route[1] 是後面項
            self._routes[point.item] = self.Route(route[0], point)
        except KeyError:
            # 此item的第一個node;開始新的route
            self._routes[point.item] = self.Route(point, point)

    def items(self):

        # tree中的每個項生成一個2位元組。 位元元組的第一個元素是item本身，第二個元素是一個生成器，它將生成樹中屬於該項的node
        for item in self._routes.keys():
            yield (item, self.nodes(item))

    def nodes(self, item):
        
        # 生成包含給定項的node序列
        try:
            node = self._routes[item][0]
        except KeyError:
            return

        while node:
            yield node
            node = node.neighbor

    def prefix_paths(self, item):
        
        # 生成以給定項結束的前面paths
        def collect_path(node):
            path = []
            while node and not node.root:
                path.append(node)
                node = node.parent
            path.reverse()
            return path

        return (collect_path(node) for node in self.nodes(item))

    def inspect(self):
        print('Tree:')
        self.root.inspect(1)
        print('Routes:')
        for item, nodes in self.items():
            print('%r' % item)
            for node in nodes:
                print('%r' % node)

def conditional_tree_from_paths(paths):
    
    # 從給定的前面paths建立FP樹條件
    tree = FPTree()
    condition_item = None
    items = set()

    # 將paths中的node導入新的tree 只有leaf的數量重要 剩餘的數量將從leaf數量重建。
    for path in paths:
        if condition_item is None:
            condition_item = path[-1].item

        point = tree.root
        for node in path:
            next_point = point.search(node.item)
            if not next_point:
                # 增加新node到tree上
                items.add(node.item)
                count = node.count if node.item == condition_item else 0
                next_point = FPNode(tree, node.item, count)
                point.add(next_point)
                tree._update_route(next_point)
            point = next_point

    assert condition_item is not None

    # 計算非leaf node的數量
    for path in tree.prefix_paths(condition_item):
        count = path[-1].count
        for node in reversed(path[:-1]):
            node._count += count

    return tree

class FPNode(object):
    
    # FP tree中的node
    def __init__(self, tree, item, count=1):
        self._tree = tree
        self._item = item
        self._count = count
        self._parent = None
        self._children = {}
        self._neighbor = None

    def add(self, child):
        
        # 將給定的FP Node child 添加為此node的child node。
        if not isinstance(child, FPNode):
            raise TypeError("Can only add other FP_Nodes as children")
            
        if not child.item in self._children:
            self._children[child.item] = child
            child.parent = self

    def search(self, item):
       
        # 檢查此node是否包含給定項的子節點 如果是，則返回該節點 否則返回“None”
        try:
            return self._children[item]
        except KeyError:
            return None

    def __contains__(self, item):
        return item in self._children

    @property
    def tree(self):
        # 此node出現的tree
        return self._tree

    @property
    def item(self):
        # 此node中包含的item
        return self._item

    @property
    def count(self):
        # 與此node item的關聯數量
        return self._count

    def increment(self):
        # 增加與此node item的關聯數量
        if self._count is None:
            raise ValueError("Root nodes have no associated count.")
        self._count += 1

    @property
    def root(self):
        # 如果此node是root則為True 否則為false
        return self._item is None and self._count is None

    @property
    def leaf(self):
        # 如果此node是leaf則為True 否則為false
        return len(self._children) == 0

    @property
    def parent(self):
        # node的parent
        return self._parent

    @parent.setter
    def parent(self, value):
        if value is not None and not isinstance(value, FPNode):
            raise TypeError("A node must have an FPNode as a parent.")
        if value and value.tree is not self.tree:
            raise ValueError("Cannot have a parent from another tree.")
        self._parent = value

    @property
    def neighbor(self):
        # node的neighbor tree中具有相同值的“右側”
        return self._neighbor

    @neighbor.setter
    def neighbor(self, value):
        if value is not None and not isinstance(value, FPNode):
            raise TypeError("A node must have an FPNode as a neighbor.")
        if value and value.tree is not self.tree:
            raise ValueError("Cannot have a neighbor from another tree.")
        self._neighbor = value

    @property
    def children(self):
        # 作為此node的child node
        return tuple(self._children.itervalues())

    def inspect(self, depth=0):
        print(('  ' * depth) + repr(self))
        for child in self.children:
            child.inspect(depth + 1)

    def __repr__(self):
        if self.root:
            return "<%s (root)>" % type(self).__name__
        return "<%s %r (%r)>" % (type(self).__name__, self.item, self.count)

if __name__ == '__main__':
    
    with open(r'D:\IBM\data.ascii.ntrans_10.tlen_10.nitems_3.csv') as csvfile:

      # 讀取CSV檔案內容
      rows = csv.reader(csvfile)	
      dataset = []
      # 以迴圈輸出每一列
      for row in rows:
          dataset.append (row)
  
    #用find_frequent_itemsets()產生frequent_itemsets
    #min_support表示設定的最小支持度，若支持度大於等於inimum_support保存此否則刪除
    #include_support表示返回結果是否包含支持度，若include_support=True
    #返回结果中包含itemset和support，否則只返回itemset
    
    frequent_itemsets = find_frequent_itemsets(dataset, min_support=45, include_support=True)
    print(type(frequent_itemsets))   # print type
    result = []
    for itemset, support in frequent_itemsets:    # 將generator结果存入list
        result.append((itemset, support))

    result = sorted(result, key=lambda i: i[0])   # 排序後输出
    for itemset, support in result:
        print(str(itemset) + ' ' + str(support))
