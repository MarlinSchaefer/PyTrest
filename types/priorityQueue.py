import numpy as np

class PriorityQueue(object):
    def __init__(self, data=None, sort_type='ascending'):
        self.priorities = []
        self.prio_queue = []
        self.noprio_queue = []
        self.sort_type = sort_type
        if data is not None:
            for dat in data:
                self.enqueue(*dat)
    
    def __len__(self):
        return len(self.prio_queue) + len(self.noprio_queue)
    
    @property
    def sort_type(self):
        return self._sort_type
    
    @sort_type.setter
    def sort_type(self, sort_type):
        if not isinstance(sort_type, str):
            raise TypeError
        if sort_type.lower() not in ['ascending', 'descending']:
            raise ValueError
        self._sort_type = sort_type.lower()
        idxs = list(np.argsort(self.priorities))
        if self.sort_type == 'descending':
            idxs.reverse()
        tmp_prio = []
        tmp_queue = []
        for idx in idxs:
            tmp_prio.append(self.priorities[idx])
            tmp_queue.append(self.prio_queue[idx])
        self.priorities = tmp_prio
        self.prio_queue = tmp_queue
    
    @property
    def max_priority(self):
        return max(self.priorities)
    
    @property
    def min_priority(self):
        return min(self.priorities)
    
    @property
    def next_priority(self):
        self.priorities[0]
    
    def enqueue(self, value, priority=None):
        if priority is None:
            self.noprio_queue.append(value)
        else:
            tmp_prio = self.priorities.copy()
            if self.sort_type == 'descending':
                tmp_prio.reverse()
            tmp_idx = np.searchsorted(tmp_prio, priority, side='right')
            if self.sort_type == 'descending':
                idx = len(self.priorities) - tmp_idx
            else:
                idx = tmp_idx
            
            self.priorities.insert(idx, priority)
            self.prio_queue.insert(idx, value)
    
    def dequeue(self):
        if len(self) > 0:
            if len(self.prio_queue) > 0:
                self.priorities.pop(0)
                return self.prio_queue.pop(0)
            else:
                return self.noprio_queue.pop(0)
        else:
            raise StopIteration
    
    def __next__(self):
        return self.dequeue()
    
    def __iter__(self):
        return self
    
    def as_list(self):
        return self.prio_queue + self.noprio_queue
            
