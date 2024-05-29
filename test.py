import torch
import os
import argparse
from datasets.crowd import Crowd
from nets.RGBTCCNet import ThermalRGBNet
from utils.raw_evaluation import eval_game
import numpy as np
import math

parser = argparse.ArgumentParser(description='Test')
parser.add_argument('--data-dir', default='F:/DataSets/RGBT_CC',
                        help='training data directory')
parser.add_argument('--save-dir', default='./ckpts_PVTV2_r224/0727-104422',
                        help='model directory')
parser.add_argument('--model', default='best_model_10.762619034647942.pth'
                    , help='model name')
parser.add_argument('--img_size', default=224, type=int, help='network input size')
parser.add_argument('--device', default='0', help='gpu device')
args = parser.parse_args()

if __name__ == '__main__':

    datasets = Crowd(os.path.join(args.data_dir, "new_test_224"), method='test')
    print('datasets', len(datasets))
    dataloader = torch.utils.data.DataLoader(datasets, 1, shuffle=False,
                                             num_workers=0, pin_memory=False)
    print('dataloader', len(dataloader))

    os.environ['CUDA_VISIBLE_DEVICES'] = args.device  # set vis gpu
    device = torch.device('cuda')

    model = ThermalRGBNet()
    model.to(device)
    model_path = os.path.join(args.save_dir, args.model)
    checkpoint = torch.load(model_path, device)
    model.load_state_dict(checkpoint, strict=False)
    model.eval()

    print('testing...')
    # Iterate over data.
    result_list = []
    with open('ans.txt', 'w') as f:
        for idx, (inputs, _, name) in enumerate(dataloader):
            if type(inputs) == list:
                inputs[0] = inputs[0].to(device)
                inputs[1] = inputs[1].to(device)
            else:
                inputs = inputs.to(device)
            if len(inputs[0].shape) == 5:
                inputs[0] = inputs[0].squeeze(0)
                inputs[1] = inputs[1].squeeze(0)
            if len(inputs[0].shape) == 3:
                inputs[0] = inputs[0].unsqueeze(0)
                inputs[1] = inputs[1].unsqueeze(0)
            with torch.set_grad_enabled(False):
                count, outputs, _ = model(inputs)  # outputs batch_size为4
                outputs1 = torch.cat((outputs[0], outputs[1]), dim=1)
                outputs2 = torch.cat((outputs[2], outputs[3]), dim=1)
                outputs3 = torch.cat((outputs[4], outputs[5]), dim=1)
                outputs = torch.cat((outputs1, outputs2, outputs3), dim=2)

                res = torch.sum(outputs).item()
                print(f'{name[0]}: {res}')
                result_list.append((int(name[0]), res))

        result_list.sort(key=lambda x: x[0])
        for name, res in result_list:
            f.write(f'{name},{res}\n')
            
