import numpy as np
import copy
from collections import deque

class UE:
    def __init__(self, buffer_size):
        self.buffer = deque(maxlen=buffer_size)
        self.buffer_size = buffer_size
        self.packets_dropped = 0
        self.packets_transmitted = 0
        self.waiting_for_ack = False
        self.has_sg = False
        
        # 时序相关变量
        self.sg_processing_delay = 1  # SG处理延迟
        self.sg_receive_time = None   # SG接收时间
        self.transmission_delay = 1    # 数据传输延迟
        self.transmission_start_time = None  # 传输开始时间

        # 动作相关变量
        self.phy_act = None
        self.dcm_act = None
        self.ucm_act = None
        
    def add_sdu(self):
        if len(self.buffer) < self.buffer_size:
            self.buffer.append(1)
            return True
        else:
            self.packets_dropped += 1
            return False
    
    def can_send_sr(self):
        return len(self.buffer) > 0 and not self.waiting_for_ack and not self.has_sg
    
    def receive_sg(self, current_time):
        self.has_sg = True
        self.sg_receive_time = current_time
    
    def can_transmit(self, current_time):
        if self.has_sg and self.sg_receive_time is not None:
            # 检查是否已经过了SG处理延迟
            return current_time >= self.sg_receive_time + self.sg_processing_delay
        return False
    
    def transmit_sdu(self, current_time):
        if len(self.buffer) > 0 and self.can_transmit(current_time):
            self.waiting_for_ack = True
            self.has_sg = False
            self.transmission_start_time = current_time
            return True
        return False
    
    def can_receive_ack(self, current_time):
        if self.waiting_for_ack and self.transmission_start_time is not None:
            # 检查是否已经过了传输延迟
            return current_time >= self.transmission_start_time + self.transmission_delay
        return False
    
    def receive_ack(self, current_time):
        if self.can_receive_ack(current_time):
            self.buffer.popleft()
            self.packets_transmitted += 1
            self.waiting_for_ack = False
            self.transmission_start_time = None
            return True
        return False

class BaseStation:
    def __init__(self, num_ues, buffer_size, arrival_prob):
        self.ues = [UE(buffer_size) for _ in range(num_ues)]
        self.arrival_prob = arrival_prob
        self.sr_queue = set()
        self.current_transmitting = None
        self.sg_delay = 1  # SG发送延迟
        self.sg_send_times = {}  # 记录每个UE的SG发送时间

        self.num_UEs = num_ues
        self.recent_k = 2
        self.reset()

    def reset(self):
        self.UE_obs = np.zeros((self.num_UEs,), dtype=np.int32)
        self.BS_obs = np.zeros((1,), dtype=np.int32)
        self.UE_actions = np.zeros((self.num_UEs,), dtype=np.int32)
        self.BS_msg = np.zeros((self.num_UEs,), dtype=np.int32)
        self.UE_msg = np.zeros((self.num_UEs,), dtype=np.int32)

        self.trajact_UE_obs = [copy.deepcopy(self.UE_obs) for _ in range(self.recent_k + 1)]
        self.trajact_UE_actions = [copy.deepcopy(self.UE_actions) for _ in range(self.recent_k + 1)]
        self.trajact_BS_obs = [copy.deepcopy(self.BS_obs) for _ in range(self.recent_k + 1)]
        self.trajact_BS_msg = [copy.deepcopy(self.BS_msg) for _ in range(self.recent_k + 1)]
        self.trajact_UE_msg = [copy.deepcopy(self.UE_msg) for _ in range(self.recent_k + 1)] 


    def step(self, current_time):
        # 1. SDU到达过程
        for ue in self.ues:
            ue.ucm_act = None
            ue.dcm_act = None
            ue.phy_act = None
            if np.random.random() < self.arrival_prob:
                ue.add_sdu()
        print(f"\nStep {current_time}:")
        print(f"Buffer lengths: {[len(ue.buffer) for ue in self.ues]}")
        # 2. 处理当前传输
        if self.current_transmitting is not None:
            ue = self.ues[self.current_transmitting]
            if ue.can_receive_ack(current_time):
                if np.random.random() < 0.9:  # 传输成功率0.9
                    ue.receive_ack(current_time)
                    ue.phy_act = 'Delete'
                    ue.dcm_act = 'ACK'
                else:
                    ue.waiting_for_ack = False
                    ue.transmission_start_time = None
                self.current_transmitting = None
        
        # 3. 收集SR
        new_sr_queue = set()
        for i, ue in enumerate(self.ues):
            if ue.can_send_sr():
                new_sr_queue.add(i)
                ue.ucm_act = 'SR'
        self.sr_queue = new_sr_queue
        
        # 4. 发送调度许可（SG）
        if self.sr_queue:
            # 随机选择一个UE发送SG
            selected_ue = np.random.choice(list(self.sr_queue))
            self.ues[selected_ue].dcm_act = 'SG' if self.ues[selected_ue].dcm_act == None else self.ues[selected_ue].dcm_act
            # 检查是否满足SG发送延迟要求
            if current_time >= self.sg_send_times.get(selected_ue, 0) + self.sg_delay:
                self.ues[selected_ue].receive_sg(current_time)
                self.sg_send_times[selected_ue] = current_time
                self.sr_queue.remove(selected_ue)
        
        # 5. 数据传输
        if self.current_transmitting is None:  # 只有当前没有传输时才开始新的传输
            for i, ue in enumerate(self.ues):
                if ue.transmit_sdu(current_time):
                    self.current_transmitting = i
                    ue.phy_act = 'Transmit'
                    break
        print(f'UE pysical actions: {[ue.phy_act for ue in self.ues]}',end=' ')
        print(f'UCM actions: {[ue.ucm_act for ue in self.ues]}',end=' ')
        print(f'DCM actions: {[ue.dcm_act for ue in self.ues]}',end=' ')
        # # 6. 获取观测
        # self.trajact_UE_obs.append(copy.deepcopy(np.array([len(ue.buffer) for ue in self.ues])))

    def get_statistics(self):
        total_transmitted = sum(ue.packets_transmitted for ue in self.ues)
        total_dropped = sum(ue.packets_dropped for ue in self.ues)
        buffer_occupancy = [len(ue.buffer) for ue in self.ues]
        sr_queue_size = len(self.sr_queue)
        return total_transmitted, total_dropped, buffer_occupancy, sr_queue_size

def run_simulation(num_ues, buffer_size, arrival_prob, num_steps):
    bs = BaseStation(num_ues, buffer_size, arrival_prob)
    
    repititions = 1
    avg_goodput = 0
    for _ in range(repititions):
        for step in range(num_steps):
            # 执行步骤
            bs.step(step)
        transmitted, dropped, occupancy, sr_queue_size = bs.get_statistics()
        avg_goodput += transmitted / (num_steps+1)

    print(f"Total packets transmitted: {avg_goodput/repititions:.3f} packets/step")
    # print(f"Total packets dropped: {dropped}")
    # print(f"Buffer occupancy: {occupancy}")
    # print(f"SR queue size: {sr_queue_size}")
    # print(f"Average throughput: {transmitted/(step+1):.3f} packets/step")

# 运行模拟
if __name__ == "__main__":
    # 设置参数
    L = 2       # UE数量
    B = 20      # 缓冲区大小
    T = 24     # 模拟步数
    pa = 11/T    # SDU到达概率

    
    run_simulation(L, B, pa, T)