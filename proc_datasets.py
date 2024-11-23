import json

def create_training_sample(state, action):
        # 构造输入文本
    input_text = f"""System state:
    - UEs: {state['num_UEs']}
    - Time step: {state['time_step']}
    - UE buffer: {describe_buffer_state(state['ue_obs_history'][-1])}
    - UE PHY actions: {describe_actions(state['ue_actions_history'][-1])}
    - Last UE UCM: {describe_ucm_actions(state['ue_msg_history'][-1])}
    - Last BS DCM: {describe_dcm_actions(state['bs_msg_history'][-1])}
    - Data channel: {describe_bs_state(state['bs_obs_history'][-1],state['num_UEs'])}

    Depending on the system state, make the following decisions:
    1. Each UE's PHY actions (transmit/delete/none)
    2. Each UE's UCM (UCM0/UCM1)
    3. BS DCM to each UE (DCM0/DCM1/DCM2)
    """

    # 替换 UCM 和 DCM 的值
    ucm_mapping = {'SR': 'UCM0', None: 'UCM1'}
    dcm_mapping = {'SG': 'DCM0', 'ACK': 'DCM1', None: 'DCM2'}
    ue_ucm = [ucm_mapping[ucm] for ucm in action['ucm']]
    ue_dcm = [dcm_mapping[dcm] for dcm in action['dcm']]
    # 构造输出文本
    decisions = ", ".join([f"UE{i}: PHY={phy}, UCM={ucm}, DCM={dcm}" for i, (phy, ucm, dcm) in enumerate(zip(action['ue_actions'], ue_ucm, ue_dcm))])
    output_text = f"""Decisions:
    {decisions}
    """
    return {
        "instruction": "As a 5G/6G scheduler, make scheduling decisions for UEs and BS based on the system state.",
        "input": input_text,
        "output": output_text
    }

# 辅助函数
def describe_buffer_state(buffer_state):
    return ", ".join([f"UE{i}'s buffer: {buf}" for i, buf in enumerate(buffer_state)])
def describe_actions(actions):
    return ", ".join([f"UE{i}: {act}" for i, act in enumerate(actions)])
def describe_ucm_actions(ucm_actions):
    return ", ".join([f"UE{i}: {act}" for i, act in enumerate(ucm_actions)])
def describe_dcm_actions(dcm_actions):
    return ", ".join([f"UE{i}: {act}" for i, act in enumerate(dcm_actions)])
def describe_bs_state(bs_state,num_ues):
    if bs_state[0] == 0:
        return "No UE is transmitting."
    elif bs_state[0] == num_ues+1:
        return f"Collision happened."
    else:
        return f"UE{bs_state[0]} is transmitting."

if __name__ == "__main__":
    file_path = 'signaling_dataset_UE2.json'
    # 读取 JSON 文件
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    proc_datasets = []
    for sample in data:
        proc_datasets.append(create_training_sample(sample['state'], sample['action']))
    with open('processed_datasets.json', 'w') as f:
        json.dump(proc_datasets, f, indent=4)