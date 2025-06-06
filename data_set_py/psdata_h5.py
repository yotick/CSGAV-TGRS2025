# GPL License
# Copyright (C) 2021 , UESTC
# All Rights Reserved
# @Author  : Xiao Wu, LiangJian Deng
# @reference:
import glob
import torch
from torch.utils.data import DataLoader


class PansharpeningSession():
    def __init__(self, args):
        self.dataloaders = {}
        self.samples_per_gpu = args.samples_per_gpu
        self.workers_per_gpu = args.workers_per_gpu
        # self.patch_size = args.patch_size
        self.writers = {}
        self.args = args

    def get_dataloader(self, dataset_name, distributed):

        if any(list(map(lambda x: x in dataset_name, ['wv2', 'wv3', 'wv4', 'qb', 'gf2']))):
            if "hp" in dataset_name:
                # high-pass filter
                from data_set_py.dataset_hp_h5 import Dataset_Pro
                dataset_name = dataset_name.split('_')[0]  # 'wv2_hp'
                dataset = Dataset_Pro('/'.join([self.args.data_dir, 'training_data_dlj', f'train_{dataset_name}.h5']),
                                      img_scale=self.args.img_range)
            else:

                from data_set_py.dataset_h5 import Dataset_Pro
                # dataset = Dataset_Pro('/'.join([self.args.data_dir, 'training_data_dlj', f'train_{dataset_name}.h5']), img_scale=self.args.img_range)
                dataset = Dataset_Pro(('./Source Data/training_data_dlj/' + f'train_{dataset_name}.h5'),
                                      img_scale=self.args.img_range)

        else:
            print(f"train_{dataset_name} is not supported.")
            raise NotImplementedError

        sampler = None
        if distributed:
            sampler = torch.utils.data.distributed.DistributedSampler(dataset)

        # if not dataset_name in self.dataloaders:
        dataloaders = \
            DataLoader(dataset, batch_size=self.samples_per_gpu,
                       persistent_workers=(True if self.workers_per_gpu > 0 else False), pin_memory=True,
                       shuffle=(sampler is None), num_workers=self.workers_per_gpu, drop_last=True, sampler=sampler)

        return dataloaders, sampler

    def get_eval_dataloader(self, dataset_name, distributed):

        if 'valid' in dataset_name:
            if "hp" in dataset_name:
                from data_set_py.dataset_hp_h5 import Dataset_Pro
                dataset = Dataset_Pro(('./Source Data/training_data_dlj/' + f'{dataset_name}.h5'),
                                      img_scale=self.args.img_range)

            else:
                from data_set_py.dataset_h5 import Dataset_Pro
                dataset = Dataset_Pro(('./Source Data/validation_data_dlj/' + f'{dataset_name}.h5'),
                                      img_scale=self.args.img_range, max_samples=10)

        elif 'test' in dataset_name:
            if 'OrigScale' in dataset_name:
                satellite = dataset_name.split('_')[-2]
                from data_set_py.ps_evaluate import MultiExmTest_full
                dataset = MultiExmTest_full((
                                                        './Source Data/test_data_dlj/' + satellite.upper() + '/full_examples/' + f'{dataset_name}_multiExm.h5'),
                                            dataset_name, img_scale=self.args.img_range)
            else:
                if 'hp' in dataset_name:
                    satellite = dataset_name.split('_')[-2]
                else:
                    satellite = dataset_name.split('_')[-1]

                from data_set_py.ps_evaluate import MultiExmTest_h5
                dataset = MultiExmTest_h5((
                        './Source Data/test_data_dlj/' + satellite.upper() + '/reduced_examples/' + f'{dataset_name}_multiExm.h5'),
                    dataset_name, img_scale=self.args.img_range)

        elif 'RR' in dataset_name or 'FR' in dataset_name:
            splits = dataset_name.split('_')
            if 'hp' in dataset_name:
                satellite = splits[-3]
            else:
                satellite = splits[-2]

            from UDL.pansharpening.evaluation.ps_evaluate import SingleDataset

            dataset = SingleDataset(['/'.join([self.args.data_dir, 'test_data', satellite.lower(),
                                               dataset_name.replace('_hp', '') + ".mat"])], dataset_name,
                                    img_scale=self.args.img_range)


        else:
            print(f"{dataset_name} is not supported.")
            raise NotImplementedError

        sampler = None
        if distributed:
            sampler = torch.utils.data.distributed.DistributedSampler(dataset)

        # if not dataset_name in self.dataloaders:
        dataloaders = \
            DataLoader(dataset, batch_size=self.samples_per_gpu,
                       shuffle=False, num_workers=1, drop_last=False, sampler=sampler)
        return dataloaders, sampler


if __name__ == '__main__':
    # from option import args
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()
    args.samples_per_gpu = 8
    args.workers_per_gpu = 0
    args.data_dir = "C:/Datasets/pansharpening_2"
    args.dataset = 'gf2'

    # survey
    # wv3 9714 16-64
    # wv2 15084 16-64
    # gf2 19809 16-64
    # qb  17139 16-64
    sess = PansharpeningSession(args)
    train_loader, _ = sess.get_test_dataloader(args.dataset, False)
    print(len(train_loader))

    # import scipy.io as sio
    #
    # x = sio.loadmat("D:/Datasets/pansharpening/training_data/train1.mat")
    # print(x.keys())
