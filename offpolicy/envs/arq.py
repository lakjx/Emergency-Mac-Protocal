import numpy as np
import os
import argparse
from html import parser
import torch
from macprotocol import UE



def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rho', type=int, default=3)
    parser.add_argument('--recent_k', type=int, default=0)
    parser.add_argument('--UE_num', type=int, default=2)
    parser.add_argument('--UE_txbuff_len', type=int, default=5)
    parser.add_argument('--UE_max_generate_SDUs', type=int, default=2)
    parser.add_argument('--p_SDU_arrival', type=float, default=0.5)
    parser.add_argument('--tbl_error_rate', type=float, default=0.01)
    parser.add_argument('--TTLs', type=int, default=24)
    parser.add_argument('--UCM', type=int, default=None)
    parser.add_argument('--DCM', type=int, default=None)
    args = parser.parse_args()
    return args
def generate_random_onehot(length):
    # 创建一个全零的数组
    onehot = np.zeros(length, dtype=int)
    # 随机选择一个索引，将其设置为 1
    random_index = np.random.randint(0, length)
    onehot[random_index] = 1
    return onehot

if __name__ == "__main__":
    args = get_parser()
    ue_group = [UE(i, args) for i in range(args.UE_num)]
    cur_ucm=[-1]*args.UE_num
    last_ucm=[-1]*args.UE_num
    # cur_dcm = [-1]*args.UE_num
    # last_dcm = [-1]*args.UE_num
    up_sig = {'None':0,'SR':1}
    ue_act = {'None':0, 'Tx':1, 'Del':2}
    sdus_received = [] 
    step = 0
    while step < args.TTLs:
        del_flag = [False]*args.UE_num
        print('step:', step)
        # UE generate SDUs
        new_gen_datalist = []
        for ue in ue_group:
            if not ue.is_already_generated() and np.random.rand() < args.p_SDU_arrival:
                cur_gen_data = ue.generate_SDU()
            else:
                cur_gen_data = None
            new_gen_datalist.append(cur_gen_data)
        print('new_gen_data:', new_gen_datalist)
        print('UE{} buff:'.format(ue_group[0].name_id), ue_group[0].buff)
        print('UE{} buff:'.format(ue_group[1].name_id), ue_group[1].buff)
        if len(sdus_received) == args.UE_num*args.UE_max_generate_SDUs and all([ue.is_done() for ue in ue_group]):
            break
        # signal transmission
        sch_idx = []
        for ue in ue_group:
            #data deletion
            if ue.ACK:
                ue.delete_SDU()
                ue.ACK = False
                del_flag[ue.name_id] = True
            if len(ue.buff) > 0:
                if last_ucm[ue.name_id] != 1 and ue.buff[0] != new_gen_datalist[ue.name_id]:
                    sig = up_sig['SR']
                else:
                    sig = up_sig['None']
            else:
                sig = up_sig['None']
            cur_ucm[ue.name_id] = sig
            if last_ucm[ue.name_id] == 1:
                sch_idx.append(ue.name_id)
    
        # data transmission
        if len(sch_idx) == 1:
            sch_ue = ue_group[sch_idx[0]]
            sch_ue.SG = True 
        elif len(sch_idx) > 1:
            sch_ue = ue_group[np.random.choice(sch_idx)]
            sch_ue.SG = True 
        else:
            sch_ue = None

        if sch_ue is not None:
            if sch_ue.buff[0] != new_gen_datalist[sch_ue.name_id]:
                dat = sch_ue.transmit_SDU()
                if dat is not None and np.random.rand() > args.tbl_error_rate :
                    sdus_received.append(dat)
                    sch_ue.buff_to_be_transmit.remove(dat)
                    # cur_dcm[sch_ue.name_id] = 1
                    sch_ue.SG = False
                    sch_ue.ACK = True  
        
        # update
        last_ucm = cur_ucm[:]
        # last_dcm = cur_dcm
        step += 1
        print('sdus_received:', sdus_received)
        

        


            
            


    