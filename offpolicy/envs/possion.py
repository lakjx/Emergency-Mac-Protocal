import random

class UE:
    def __init__(self, id, buffer_size):
        self.id = id
        self.buffer = []  # 初始传输缓冲区为空
        self.has_sg = False  # 是否获得调度许可
        self.sr_sent = False  # 是否发送了调度请求
        self.data_to_transmitted = None  # 成功传输的数据
        self.ack_received = False  # 是否收到ACK

        self.buffer_size = buffer_size  # 缓冲区大小
        self.gen_data_count = 0  # 生成的数据包数量
        self.Nrx = 0
    
    def generate_data(self, arrival_prob):
        if random.random() < arrival_prob and len(self.buffer) < self.buffer_size:
            new_data = f'TB{self.id}_{self.gen_data_count}'
            self.gen_data_count += 1
            self.buffer.append(new_data)
    
    def send_sr(self):
        """发送调度请求,如果缓冲区非空则发送"""
        if len(self.buffer) > 0:
            self.sr_sent = True
            return True
        return False

    def buffer_manage(self):
        if self.has_sg and len(self.buffer) > 0:
            self.has_sg = False
            self.data_to_transmitted = self.buffer.pop(0)
            print(f"UE {self.id}发送数据:{self.data_to_transmitted}")
            return self.data_to_transmitted
        elif self.ack_received and len(self.buffer) > 0:
            delt = self.buffer.pop(0)
            print(f"UE {self.id}删除数据:{delt}")
            self.ack_received = False
            return None
        return None

class BS:
    def __init__(self):
        self.ue_list = []  # 存储所有的UE
        self.sr_ue_list = []  # 存储上一时间步发送了SR的UE
        self.pending_transmissions = []  # 存储已授权传输的UE（等待传输）
        self.pending_acks = []  # 存储等待发送ACK的UE

    def add_ue(self, ue):
        self.ue_list.append(ue)

    def receive_srs(self):
        # 在当前时间步,接收来自所有UE的SR
        current_sr_list = [ue for ue in self.ue_list if ue.send_sr()]
        sr_ids = [ue.id for ue in current_sr_list]
        if sr_ids:
            print(f"BS收到来自 UE {sr_ids} 的SR")
        else:
            print("BS没有收到调度请求SR")
        return current_sr_list


    def send_acks(self):
        for ue in self.pending_acks:
            print(f"BS:收到 UE {ue.id} 的数据 {ue.data_transmitted},发送 ACK")
            ue.receive_ack()
        # 清空 ACK 队列
        self.pending_acks.clear()


def simulate(num_ue, num_steps, data_arrival_prob, transmit_success_prob,ue_txbuff_len=5):
    # 创建基站和UE
    bs = BS()
    ues = [UE(i,ue_txbuff_len) for i in range(num_ue)]
    rec_sdu = []

    # 将UE添加到基站
    for ue in ues:
        bs.add_ue(ue)

    # 初始化上一时间步的调度请求列表为空
    last_sr_ue_list = []
    last_data_channel = []
    # 模拟多个时间步
    for step in range(num_steps):
        print(f"\n时间步 {step + 1}:")

        # 每个 UE 根据到达概率生成新的数据包
        data_channel = []
        for ue in ues:
            ue.generate_data(data_arrival_prob)
            if ue.ack_received:
                ue.buffer.pop(0)
            if ue.has_sg:
                txdata = ue.buffer.pop(0)
        
        for ue in ues:
            print(f"UE {ue.id}缓冲区: {ue.buffer}")
        print(f"BS received SDUs: {rec_sdu}")

        bs.sr_ue_list = last_sr_ue_list.copy() 
        last_sr_ue_list = bs.receive_srs()
        
        data_channel = last_data_channel.copy()
        last_data_channel.clear()

        # for ue in ues:
        #     tx_data = ue.buffer_manage()
        #     if tx_data:
        #         last_data_channel.append(ue)
        
        last_sr_ue_list = bs.receive_srs()
    
        if data_channel:
            assert len(data_channel) == 1
            selected_ue = data_channel[0]
            if random.random() < transmit_success_prob:
                rec_sdu.append(selected_ue.data_to_transmitted)
                print(f"BS:发送ACK给UE{selected_ue.id}")
                selected_ue.ack_received = True
            else:
                #未传输成功，data_to_transmitted放回缓冲区
                # selected_ue.buffer.insert(0,selected_ue.data_to_transmitted)
                selected_ue.ack_received = False

        if bs.sr_ue_list:
            selected_ue = random.choice(bs.sr_ue_list)
            if selected_ue in data_channel:
                selected_ue.has_sg = False
            else:
                print(f"BS:发送SG给UE{selected_ue.id}")
                selected_ue.has_sg = True
        else:
            print("BS:没有调度许可 (SG) 发送")
    
    total_Rx = len(rec_sdu)
    return total_Rx/num_steps

# 运行模拟
rep = 10
Goodput = 0
for _ in range(rep):
    Goodput = Goodput + simulate(num_ue=2, num_steps=24, data_arrival_prob=0.3, transmit_success_prob=0.9,ue_txbuff_len=20)

print("Goodput:{}".format(Goodput/rep))
# gp = simulate(num_ue=2, num_steps=24, data_arrival_prob=0.41, transmit_success_prob=0.99,ue_txbuff_len=20)
# print("Goodput:{}".format(gp))