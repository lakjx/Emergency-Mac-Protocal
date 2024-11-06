import random

class UE:
    def __init__(self, id, buffer_capacity, sdu_gen_prob):
        self.id = id
        self.buffer_capacity = buffer_capacity  # 缓冲区容量
        self.sdu_gen_prob = sdu_gen_prob  # 生成SDU的概率
        self.buffer = []  # 存储待发送的SDU
        self.total_sdu_generated = 0  # 已生成的SDU数量
        self.sr_sent = False  # 是否已发送SR
        self.successful_transmissions = 0  # 成功传输的SDU数量
        self.sdu_generated_this_step = False  # 本时间步是否生成了SDU

    def generate_sdu(self):
        """根据概率生成SDU并放入传输缓冲区"""
        if len(self.buffer) < self.buffer_capacity:
            if random.random() < self.sdu_gen_prob:
                self.buffer.append("SDU")
                self.total_sdu_generated += 1
                self.sdu_generated_this_step = True  # 标记为本时间步生成了SDU
            else:
                self.sdu_generated_this_step = False  # 没有生成SDU
        else:
            self.sdu_generated_this_step = False  # 没有生成SDU

    def send_scheduling_request(self):
        """如果缓冲区不为空且本时间步未生成新的SDU 则发送调度请求"""
        if len(self.buffer) > 0 and not self.sdu_generated_this_step:
            self.sr_sent = True
        else:
            self.sr_sent = False

    def transmit(self, tbl_error_rate):
        """执行数据传输，模拟包擦除信道"""
        if len(self.buffer) > 0:
            # 模拟传输块错误率
            if random.random() > tbl_error_rate:
                return True  # 传输成功
        return False  # 传输失败

    def ack_received(self):
        """收到ACK后 删除一个已发送的SDU"""
        if len(self.buffer) > 0:
            self.buffer.pop(0)
            self.successful_transmissions += 1

class BaseStation:
    def __init__(self, tbl_error_rate):
        self.tbl_error_rate = tbl_error_rate  # 传输块错误率

    def schedule(self,previous_sr_queue):
        """随机选择一个UE发送调度许可"""
        if len(previous_sr_queue) > 0:
            return random.choice(previous_sr_queue)
        return None

    def process_transmissions(self, ue):
        """处理UE的传输 返回是否成功"""
        return ue.transmit(self.tbl_error_rate)

def simulate_tdma(num_ues, buffer_capacity, sdu_gen_prob, tbl_error_rate, time_steps):
    """模拟TDMA协议"""
    ues = [UE(i, buffer_capacity, sdu_gen_prob) for i in range(num_ues)]
    bs = BaseStation(tbl_error_rate)
    previous_sr_queue = []
    previous_ack_queue = []
    for t in range(time_steps):
        print(f"\nTime step {t+1}:")
        
        # 每个UE尝试生成SDU
        for ue in ues:
            ue.generate_sdu()

        # 每个UE发送调度请求
        current_sr_queue = []
        for ue in ues:
            ue.send_scheduling_request()
            if ue.sr_sent:
                current_sr_queue.append(ue)

        # 基站随机调度一个UE
        for item in previous_ack_queue:
            item.ack_received()
            if item in previous_sr_queue:
                previous_sr_queue.remove(item)
        scheduled_ue = bs.schedule(previous_sr_queue)

        current_ack_queue = []
        if scheduled_ue:
            print(f"  BS schedules UE {scheduled_ue.id} for transmission.")
            success = bs.process_transmissions(scheduled_ue)

            if success:
                current_ack_queue.append(scheduled_ue)
                print(f"  UE {scheduled_ue.id} successfully transmitted a TB.")
                # scheduled_ue.ack_received()  # 成功传输后，接收到ACK
            else:
                print(f"  UE {scheduled_ue.id} failed to transmit a TB.")

        # 清空SR队列
        bs.sr_queue = []

        # 打印当前缓冲区状态
        for ue in ues:
            print(f"  UE {ue.id} buffer: {len(ue.buffer)} SDUs, successful transmissions: {ue.successful_transmissions}")
        # 把当前的SR队列保存为上一个时间步的SR队列
        previous_sr_queue = current_sr_queue
        previous_ack_queue = current_ack_queue

    else:
        print("\nSimulation ended. Some UEs may not have transmitted all SDUs.")
    received_sdus = 0
    for ue in ues:
        received_sdus += ue.successful_transmissions
    return received_sdus/24

# 模拟参数
num_ues = 2  # 两个UE
buffer_capacity = 20  # 每个UE的缓冲区容量为20
sdu_gen_prob = 0.5 # SDU到达概率为0.5
tbl_error_rate = 0.1  # 传输块错误率为0.1 (10%失败率)
time_steps = 24  # 模拟的时间步数

# 运行模拟
avg_goodput = 0
repititions = 10
for _ in range(repititions):
    goodput=simulate_tdma(num_ues, buffer_capacity, sdu_gen_prob, tbl_error_rate, time_steps)
    avg_goodput+=goodput
print(avg_goodput/repititions)