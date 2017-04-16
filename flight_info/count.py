import time as t
import threading


class Count_info(threading.Thread):
    def __init__(self,seq_class,the_seq):
        super().__init__()
        self.seq_class = seq_class
        self.the_seq = the_seq
    def run(self):
        last_num = 0
        if self.seq_class == 'seq':
            while True:
                print('序列中现有%d个对象,本时段处理速率为%d项/秒' % (len(self.the_seq),(len(self.the_seq)-last_num)/15))
                last_num = len(self.the_seq)
                t.sleep(15)
        elif self.seq_class == 'que':
            while True:
                print('队列中现有%d个对象,本时段处理速率为%d项/秒' % (self.the_seq.qsize(),(self.the_seq.qsize()-last_num)/15))
                last_num = self.the_seq.qsize()
                t.sleep(15)

